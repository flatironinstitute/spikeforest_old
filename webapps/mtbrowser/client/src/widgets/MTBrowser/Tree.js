import React, { Component } from 'react';
import values from 'lodash/values';
import PropTypes from 'prop-types';

import TreeNode from './TreeNode';

const data = {
    '/root': {
        path: '/root',
        type: 'folder',
        isRoot: true,
        children: ['/root/david', '/root/jslancer'],
    },
    '/root/david': {
        path: '/root/david',
        type: 'folder',
        children: ['/root/david/readme.md'],
    },
    '/root/david/readme.md': {
        path: '/root/david/readme.md',
        type: 'file',
        content: 'Thanks for reading me me. But there is nothing here.'
    },
    '/root/jslancer': {
        path: '/root/jslancer',
        type: 'folder',
        children: ['/root/jslancer/projects', '/root/jslancer/vblogs'],
    },
    '/root/jslancer/projects': {
        path: '/root/jslancer/projects',
        type: 'folder',
        children: ['/root/jslancer/projects/treeview'],
    },
    '/root/jslancer/projects/treeview': {
        path: '/root/jslancer/projects/treeview',
        type: 'folder',
        children: [],
    },
    '/root/jslancer/vblogs': {
        path: '/root/jslancer/vblogs',
        type: 'folder',
        children: [],
    },
};

export default class Tree extends Component {
    constructor(props) {
        super(props);
        this.state = {
            open_node_paths: {}
        };
    }

    getChildNodes = (node) => {
        let data;
        if (!node) {
            data = this.props.data
        }
        else if (node.type === 'folder') {
            data = node.dir;
        }
        else {
            return [];
        }
        let nodes = [];
        for (let dname in data.dirs) {
            let dir0 = data.dirs[dname];
            let node0 = {
                path: `/${dname}`,
                type: 'folder',
                dir: dir0
            };
            node0.isOpen = (this.state.open_node_paths[node0.path]);
            nodes.push(node0);
        }
        for (let fname in data.files) {
            let file0 = data.files[fname];
            nodes.push({
                path: `/${fname}`,
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
        onSelect(node);
    }

    render() {
        const rootNodes = this.getChildNodes(null);
        return (
            <div>
                {rootNodes.map(node => (
                    <TreeNode
                        node={node}
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
    onSelect: PropTypes.func.isRequired,
};