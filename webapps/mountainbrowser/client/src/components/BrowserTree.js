import React, { Component } from 'react';
import Tree from './Tree.js';
const MountainClient = require('@mountainclient-js').MountainClient;
import styled from 'styled-components'

const STATUS_WAITING = 'waiting';
const STATUS_LOADED = 'loaded';
const STATUS_LOADING = 'loading';
const STATUS_FAILED_TO_LOAD = 'failed-to-load';

const HistoryLine = styled.div`
  height:8px;
  width: 100%;
  background: #E2E2E2;
  cursor: arrow;
  margin-top: 6px;

  :hover {
    background: gray;
  }
`;

class NodeCreator {
    createObjectNode(obj, name, basepath, part_of_list) {
        const max_array_children = 20;
        let childNodes = [];
        let path0 = this.joinPaths(basepath, name, '.', part_of_list);
        let type0 = 'object';
        if (Array.isArray(obj)) {
            childNodes = this.createArrayHierarchyChildNodes(obj, max_array_children, 0, obj.length, path0);
        }
        else {
            for (let key in obj) {
                let val = obj[key];
                if (typeof (val) == 'object') {
                    childNodes.push(this.createObjectNode(val, key, path0));
                }
                else {
                    childNodes.push(this.createValueNode(val, key, path0));
                }
            }
        }
        return {
            type: type0,
            name: name,
            childNodes: childNodes,
            path: path0,
            data: {
                object: obj
            }
        }
    }

    createArrayHierarchyChildNodes(X, max_array_children, i1, i2, path0) {
        let childNodes = [];
        if (i2 - i1 <= max_array_children) {
            for (let ii = i1; ii < i2; ii++) {
                let val = X[ii];
                if (typeof (val) == 'object') {
                    childNodes.push(this.createObjectNode(val, '' + ii, path0, true));
                }
                else {
                    childNodes.push(this.createValueNode(val, '' + ii, path0, true));
                }
            }
        }
        else {
            let stride = 1;
            while ((i2 - i1) / stride > max_array_children / 2) {
                stride = stride * 10;
            }
            for (let jj = i1; jj < i2; jj += stride) {
                let jj2 = jj + stride;
                if (jj2 >= i2) jj2 = i2;
                childNodes.push({
                    type: 'array-parent',
                    name: `${jj} - ${jj2 - 1}`,
                    path: path0 + `[${jj}-${jj2 - 1}]`,
                    data: {},
                    childNodes: this.createArrayHierarchyChildNodes(X, max_array_children, jj, jj2, path0),
                });
            }
        }
        return childNodes;

    }

    createValueNode(val, name, basepath) {
        let path0 = this.joinPaths(basepath, name, '.');
        return {
            type: 'value',
            name: name,
            path: path0,
            data: {
                value: val
            }
        };
    }

    createDirNode(X, name, basepath) {
        let childNodes = [];
        let path0 = this.joinPaths(basepath, name, '/');
        for (let dname in X.dirs) {
            childNodes.push(this.createDirNode(X.dirs[dname], dname, path0));
        }
        for (let fname in X.files) {
            childNodes.push(this.createFileNode(X.files[fname], fname, path0));
        }
        return {
            type: 'dir',
            name: name,
            path: path0,
            data: {
                dir: X
            },
            childNodes: childNodes
        };
    }

    createFileNode(X, name, basepath) {
        let path0 = this.joinPaths(basepath, name, '/');
        return {
            type: 'file',
            name: name,
            path: path0,
            data: {
                file: X
            },
            childNodes: []
        };
    }

    joinPaths(path1, path2, sep, part_of_list) {
        if (!path2) return path1;
        if (!path1) return path2;
        if (part_of_list) {
            return `${path1}[${path2}]`;
        }
        else {
            return `${path1}${sep}${path2}`;
        }
    }
}

class RemoteLoader {
    async loadDirectory(path) {
        let mt = new MountainClient();
        mt.configDownloadFrom(['spikeforest.public']);
    
        let X;
        if (path.startsWith('key://')) {
            path = await mt.resolveKeyPath(path);
            if (!path) return null;
        }
        if (path.startsWith('sha1dir://')) {
            let vals = path.split('/');
            vals[2] = vals[2].split('.')[0];
            X = await mt.loadObject(`sha1://${vals[2]}`);
            if (!X) return null;
            for (let i = 3; i < vals.length; i++) {
                if (vals[i]) {
                    if ((X.dirs) && (vals[i] in X.dirs)) {
                        X = X.dirs[vals[i]];
                    }
                    else {
                        return null;
                    }
                }
            }
        }
        else {
            return null;
        }
    
        return X;
    }
}

class BrowserTree extends Component {
    state = {
        status: STATUS_WAITING,
        rootNode: null
    };
    nodeCreator = new NodeCreator();
    remoteLoader = new RemoteLoader();


    async componentDidMount() {
        await this.updateContent();
    }

    async componentDidUpdate(prevProps) {
        if (this.props.path !== prevProps.path) {
            await this.updateContent()
        }
    }

    async updateContent() {
        const { path } = this.props;
        this.setState({ status: STATUS_LOADING });
        let rootNode = null;
        if (path.endsWith('.json')) {
            let mt = new MountainClient();
            mt.configDownloadFrom(['spikeforest.public']);
            let A = await mt.loadObject(path, {});
            if (!A) {
                this.setState({
                    status: STATUS_FAILED_TO_LOAD
                });
                return;
            }
            rootNode = this.nodeCreator.createObjectNode(A, '');
        }
        else {
            let X = await this.remoteLoader.loadDirectory(path, {});
            if (!X) {
                this.setState({
                    status: STATUS_FAILED_TO_LOAD
                });
                return;
            }
            rootNode = this.nodeCreator.createDirNode(X, '', path);
        }
        this.setState({
            status: STATUS_LOADED,
            rootNode: rootNode,
            selectedNode: rootNode
        });
    }

    handleNodeSelected = (node) => {
        this.setState({
            selectedNode: node
        });
        this.props.onItemSelected && this.props.onItemSelected({
            type: node.type,
            name: node.name,
            path: node.path,
            data: JSON.parse(JSON.stringify(node.data))
        });
    }

    handleHistoryLineClick(ind) {
        this.props.onGotoHistory && this.props.onGotoHistory(ind);
    }

    render() {
        const { status } = this.state;
        switch(status) {
            case STATUS_WAITING:
                return <div>Waiting to load...</div>;
            case STATUS_LOADING:
                return <div>{`Loading ${this.props.path}...`}</div>;
            case STATUS_FAILED_TO_LOAD:
                    return <div>{`Failed to load ${this.props.path}...`}</div>;
            case STATUS_LOADED:
                return (
                    <React.Fragment>
                        {
                            this.props.pathHistory.map((p, ind) => (
                                <HistoryLine key={ind} title={p} onClick={() => { this.handleHistoryLineClick(ind) }} />
                            ))
                        }
                    <Tree
                        rootNode={this.state.rootNode}
                        selectedNode={this.state.selectedNode}
                        onNodeSelected={this.handleNodeSelected}
                    />
                    </React.Fragment>
                );
        }
    }
}
 
export default BrowserTree;