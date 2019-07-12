import React from 'react';
import { FaFile, FaFolder, FaFolderOpen, FaChevronDown, FaChevronRight, FaBed, FaBullhorn } from 'react-icons/fa';
import styled from 'styled-components';
import PropTypes from 'prop-types';

const getPaddingLeft = (level, type) => {
  let paddingLeft = level * 20;
  if (type === 'file') paddingLeft += 20;
  return paddingLeft;
}

const StyledTreeNode = styled.div`
  display: flex;
  flex-direction: row;
  align-items: center;
  // padding: 5px 8px;
  margin-top: 8px;
  margin-bottom: 8px;
  margin-left: ${props => getPaddingLeft(props.level, props.type)}px;
  cursor: pointer;

  &.selected {
    background: #E2E2E2;
  }

  // &:hover {
  //   background: lightgray;
  // }
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
    return `${node.name || '/'}: ${abbreviate(node.data.value, 30)}`;
  }
  else {
    return node.name || '/';
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
      <StyledTreeNode level={level} type={node.type} className={(node === selectedNode ) ? 'selected' : '' } onClick={() => onNodeSelect(node)}>
        <NodeIcon key={'expanded-icon'} onClick={(e) => {e.stopPropagation(); onToggle(node)}}>
          { node.type === 'dir' && (isExpanded ? <FaChevronDown /> : <FaChevronRight />) }
          { node.type === 'object' && (isExpanded ? <FaChevronDown /> : <FaChevronRight />) }
          { node.type === 'array-parent' && (isExpanded ? <FaChevronDown /> : <FaChevronRight />) }
        </NodeIcon>
        
        <NodeIcon key={'item-icon'} marginRight={10}>
          { node.type === 'file' && <FaFile /> }
          { node.type === 'value' && <FaBed /> }
          { node.type === 'dir' && isExpanded && <FaFolderOpen /> }
          { node.type === 'dir' && !isExpanded && <FaFolder /> }
          { node.type === 'object' && isExpanded && <FaBullhorn /> }
          { node.type === 'object' && !isExpanded && <FaBullhorn /> }
          { node.type === 'array-parent' && isExpanded && <FaBullhorn /> }
          { node.type === 'array-parent' && !isExpanded && <FaBullhorn /> }
        </NodeIcon>
        

        <span key={'label'} role="button" style={{cursor: 'pointer'}}>
          { getNodeLabel(node) }
        </span>
      </StyledTreeNode>

      { isExpanded && getChildNodes(node).map(childNode => (
        <TreeNode 
          {...props}
          key={childNode.path}
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