import React, { Component } from 'react';
import PropTypes from 'prop-types';

import TreeNode from './TreeNode';

export default class Tree extends Component {
    constructor(props) {
        super(props);
        this.state = {
            open_node_paths: this.props.openNodePaths || {},
            selectedNodePath: this.props.selectedNodePath || null
        };
    }

    getChildNodes = (node) => {
        let data;
        let parent_path;
        if (!node) {
            data = this.props.data;
            parent_path = '';
        }
        else if (node.type === 'folder') {
            data = node.dir;
            parent_path = node.path;
        }
        else {
            return [];
        }
        let nodes = [];
        for (let dname in data.dirs) {
            let dir0 = data.dirs[dname];
            let node0 = {
                path: `${parent_path}/${dname}`,
                type: 'folder',
                dir: dir0
            };
            node0.isOpen = (this.state.open_node_paths[node0.path]);
            nodes.push(node0);
        }
        for (let fname in data.files) {
            let file0 = data.files[fname];
            nodes.push({
                path: `${parent_path}/${fname}`,
                type: 'file',
                file: file0
            });
        }
        return nodes;
    }

    onToggle = (node) => {
        const { open_node_paths } = this.state;
        open_node_paths[node.path] = !(open_node_paths[node.path]);
        this.setState({ open_node_paths });
        // const { nodes } = this.state;
        // nodes[node.path].isOpen = !node.isOpen;
        // this.setState({ nodes });
    }

    onNodeSelect = node => {
        const { onSelect } = this.props;
        this.setState({
            selectedNodePath: node.path
        });
        onSelect(node);
    }

    render() {
        const rootNodes = this.getChildNodes(null);
        return (
            <div>
                {rootNodes.map(node => (
                    <TreeNode
                        node={node}
                        selectedNodePath={this.state.selectedNodePath}
                        getChildNodes={this.getChildNodes}
                        onToggle={this.onToggle}
                        onNodeSelect={this.onNodeSelect}
                    />
                ))}
            </div>
        )
    }
}

Tree.propTypes = {
    data: PropTypes.object,
    onSelect: PropTypes.func.isRequired
};