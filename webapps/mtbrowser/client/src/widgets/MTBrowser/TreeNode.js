import React from 'react';
import { FaFile, FaFolder, FaFolderOpen, FaChevronDown, FaChevronRight, FaBed, FaBullhorn } from 'react-icons/fa';
import styled from 'styled-components';
import last from 'lodash/last';
import PropTypes from 'prop-types';
import { notDeepEqual } from 'assert';

const getPaddingLeft = (level, type) => {
  let paddingLeft = level * 20;
  if (type === 'file') paddingLeft += 20;
  return paddingLeft;
}

const StyledTreeNode = styled.div`
  display: flex;
  flex-direction: row;
  align-items: center;
  padding: 5px 8px;
  padding-left: ${props => getPaddingLeft(props.level, props.type)}px;

  &:hover {
    background: lightgray;
  }
`;

const NodeIcon = styled.div`
  font-size: 12px;
  margin-right: ${props => props.marginRight ? props.marginRight : 5}px;
`;

const abbreviate = (val, max_chars) => {
  let str0 = '' + val;
  if (str0.length > max_chars) {
    return str0.slice(0, max_chars - 3) + '...';
  }
  else {
    return str0;
  }
}

const getNodeLabel = (node) => {
  if (node.type === 'value') {
    return `${node.name || 'root'}: ${abbreviate(node.value, 30)}`;
  }
  else {
    return node.name || 'root';
  }
}

const TreeNode = (props) => {
  const { node, selectedNode, expandedNodePaths, getChildNodes, level, onToggle, onNodeSelect } = props;

  if (!node) {
    return <div>TreeNode: no node</div>;
  }

  let isExpanded = expandedNodePaths[node.path];

  return (
    <React.Fragment>
      <StyledTreeNode level={level} type={node.type} onClick={() => onNodeSelect(node)}>
        <NodeIcon onClick={() => onToggle(node)}>
          { node.type === 'dir' && (isExpanded ? <FaChevronDown /> : <FaChevronRight />) }
          { node.type === 'object' && (isExpanded ? <FaChevronDown /> : <FaChevronRight />) }
          { node.type === 'array-parent' && (isExpanded ? <FaChevronDown /> : <FaChevronRight />) }
        </NodeIcon>
        
        <NodeIcon marginRight={10}>
          { node.type === 'file' && <FaFile /> }
          { node.type === 'value' && <FaBed /> }
          { node.type === 'dir' && isExpanded && <FaFolderOpen /> }
          { node.type === 'dir' && !isExpanded && <FaFolder /> }
          { node.type === 'object' && isExpanded && <FaBullhorn /> }
          { node.type === 'object' && !isExpanded && <FaBullhorn /> }
          { node.type === 'array-parent' && isExpanded && <FaBullhorn /> }
          { node.type === 'array-parent' && !isExpanded && <FaBullhorn /> }
        </NodeIcon>
        

        <span role="button">
          { getNodeLabel(node) }
          { (node === selectedNode ) ? '*' : '' }
        </span>
      </StyledTreeNode>

      { isExpanded && getChildNodes(node).map(childNode => (
        <TreeNode 
          {...props}
          node={childNode}
          level={level + 1}
        />
      ))}
    </React.Fragment>
  );
}

TreeNode.propTypes = {
  node: PropTypes.object.isRequired,
  selectedNode: PropTypes.object.isRequired,
  expandedNodePaths: PropTypes.object.isRequired,
  getChildNodes: PropTypes.func.isRequired,
  level: PropTypes.number.isRequired,
  onToggle: PropTypes.func.isRequired,
  onNodeSelect: PropTypes.func.isRequired,
};

TreeNode.defaultProps = {
  level: 0,
};

export default TreeNode;