import React, { Component } from 'react';
import PropTypes from 'prop-types';

import TreeNode from './TreeNode';

export default class Tree extends Component {
    constructor(props) {
        super(props);
        this.state = {
            selectedNode: this.props.selectedNode || null,
            expandedNodePaths: {}
        };
    }

    componentDidMount() {
        const { expandedNodePaths } = this.state;
        expandedNodePaths[this.props.rootNode.path] = true;
        this.setState({ expandedNodePaths });
    }

    getChildNodes = (node) => {
        if (!node.childNodes) {
            return [];
        }
        return node.childNodes;
    }

    onToggle = (node) => {
        const { expandedNodePaths } = this.state;
        expandedNodePaths[node.path] = !(expandedNodePaths[node.path]);
        this.setState({ expandedNodePaths });
    }

    onNodeSelect = node => {
        const { onSelect } = this.props;
        this.setState({
            selectedNode: node
        });
        if (onSelect) {
            onSelect(node);
        }
    }

    render() {
        const { rootNode, selectedNode } = this.props
        const { expandedNodePaths } = this.state;
        if (!rootNode) {
            return <div>No root node.</div>;
        }
        return (
            <div>
                <TreeNode
                    node={rootNode}
                    selectedNode={selectedNode}
                    expandedNodePaths={expandedNodePaths}
                    getChildNodes={this.getChildNodes}
                    onToggle={this.onToggle}
                    onNodeSelect={this.onNodeSelect}
                    level={0}
                />
            </div>
        )
    }
}

Tree.propTypes = {
    rootNode: PropTypes.object.isRequired,
    selectedNode: PropTypes.object,
    onSelect: PropTypes.func
};