import React, { Component } from 'react';
import PropTypes from 'prop-types';

export default class FileView extends Component {
    constructor(props) {
        super(props);
        this.state = {
            fileContent: null,
            fileContentStatus: 'not-loading'
        };
    }

    async componentDidMount() {
    }

    async componentDidUpdate(prevProps) {
    }

    getViewPluginElements() {
        let { node } = this.props;
        let elements = [];
        if (this.props.viewPlugins) {
            for (let plugin of this.props.viewPlugins) {
                if (node.type === 'file') {
                    if ('getViewElementsForFile' in plugin) {
                        let elements0 = plugin.getViewElementsForFile(`sha1://${node.file.sha1}/${node.name}`, {size: node.file.size});
                        elements.push(...elements0);
                    }
                }
                else if (node.type === 'dir') {
                    if ('getViewElementsForDir' in plugin) {
                        let elements0 = plugin.getViewElementsForDir(node.dir, {path: node.path});
                        elements.push(...elements0);
                    }
                }
            }
        }
        return elements;
    }

    render() {
        let { node } = this.props;
        if (!node) {
            return <div></div>;
        }

        let viewPluginElements = this.getViewPluginElements();

        if (node.type === 'file') {
            let path0 = node.path;
            if (path0.endsWith('.json')) {
                path0 = <a href="#" onClick={() => {this.props.onOpenPath && this.props.onOpenPath(node.path)}}>{node.path}</a>;
            }
            return (
                <div>
                    <table className="table">
                        <tr>
                            <td>Path</td>
                            <td>{path0}</td>
                        </tr>
                        <tr>
                            <td>Size</td>
                            <td>{(node.file || {}).size}</td>
                        </tr>
                    </table>
                    <span>
                        {viewPluginElements}
                    </span>
                </div>
            )
        }
        else if (node.type === 'dir') {
            return (
                <div>
                    <table className="table">
                        <tr>
                            <td>Path</td>
                            <td><a href="#" onClick={() => {this.props.onOpenPath && this.props.onOpenPath(node.path)}}>{node.path}</a></td>
                        </tr>
                    </table>
                    <span>
                        {viewPluginElements}
                    </span>
                </div>
            )
        }
        else if (node.type === 'object') {
            return (
                <div>
                    <table className="table">
                        <tr>
                            <td>Path</td>
                            <td>{node.path}</td>
                        </tr>
                    </table>
                    <span>
                        {viewPluginElements}
                    </span>
                </div>
            )
        }
        else if (node.type === 'array-parent') {
            return (
                <div>
                    <table className="table">
                        <tr>
                            <td>Path</td>
                            <td>{node.path}</td>
                        </tr>
                    </table>
                    <span>
                        {viewPluginElements}
                    </span>
                </div>
            )
        }
        else if (node.type === 'value') {
            let val0 = node.value;
            if (isPath(val0)) {
                val0 = <a href="#" onClick={() => {this.props.onOpenPath && this.props.onOpenPath(node.value)}}>{node.value}</a>
            }
            return (
                <div>
                    <table className="table">
                        <tr>
                            <td>Path</td>
                            <td>{node.path}</td>
                        </tr>
                        <tr>
                            <td>Value</td>
                            <td>{val0}</td>
                        </tr>
                    </table>
                    <span>
                        {viewPluginElements}
                    </span>
                </div>
            )
        }
        else {
            return <div>{`Unexpected node type: ${node.type}`}</div>
        }
    }
}

function isPath(str0) {
    if (typeof(str0) != 'string') return false;
    return (str0.startsWith('sha1://') || str0.startsWith('sha1dir://') || str0.startsWith('key://'));
}

FileView.propTypes = {
    basePath: PropTypes.string,
    file: PropTypes.object,
    onOpenPath: PropTypes.func
};