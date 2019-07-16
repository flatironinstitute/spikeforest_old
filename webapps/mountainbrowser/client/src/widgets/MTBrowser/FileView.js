import React, { Component } from 'react';
import PropTypes from 'prop-types';
import { Container, Row } from 'react-bootstrap';

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
                        let elements0 = plugin.getViewElementsForFile(`sha1://${node.file.sha1}/${node.name}`, { size: node.file.size });
                        elements.push(...elements0);
                    }
                }
                else if (node.type === 'dir') {
                    if ('getViewElementsForDir' in plugin) {
                        let elements0 = plugin.getViewElementsForDir(node.dir, { path: node.path });
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

        let table;
        if (node.type === 'file') {
            let path0 = node.path;
            if (path0.endsWith('.json')) {
                path0 = <a href="#" onClick={() => { this.props.onOpenPath && this.props.onOpenPath(node.path) }}>{node.path}</a>;
            }
            table = <table className="table">
                <tbody>
                    <tr>
                        <td>Path</td>
                        <td>{path0}</td>
                    </tr>
                    <tr>
                        <td>Size</td>
                        <td>{(node.file || {}).size}</td>
                    </tr>
                </tbody>
            </table>;
        }
        else if (node.type === 'dir') {
            table = <table className="table">
                <tbody>
                    <tr>
                        <td>Path</td>
                        <td><a href="#" onClick={() => { this.props.onOpenPath && this.props.onOpenPath(node.path) }}>{node.path}</a></td>
                    </tr>
                </tbody>
            </table>;
        }
        else if (node.type === 'object') {
            table = <table className="table">
                <tbody>
                    <tr>
                        <td>Path</td>
                        <td>{node.path}</td>
                    </tr>
                </tbody>
            </table>;
        }
        else if (node.type === 'array-parent') {
            table = <table className="table">
                <tbody>
                    <tr>
                        <td>Path</td>
                        <td>{node.path}</td>
                    </tr>
                </tbody>
            </table>;
        }
        else if (node.type === 'value') {
            let val0 = node.value;
            if (isPath(val0)) {
                val0 = <a href="#" onClick={() => { this.props.onOpenPath && this.props.onOpenPath(node.value) }}>{node.value}</a>
            }
            table = <table className="table">
                <tbody>
                    <tr>
                        <td>Path</td>
                        <td>{node.path}</td>
                    </tr>
                    <tr>
                        <td>Value</td>
                        <td>{val0}</td>
                    </tr>
                </tbody>
            </table>;
        }
        else {
            return <div>{`Unexpected node type: ${node.type}`}</div>
        }

        return (
            <Container>
                <Row>
                    {table}

                </Row>
                {viewPluginElements.map((elmt, ii) => (
                    <Row key={`elmt-${ii}`}>
                        {elmt}
                    </Row>
                ))}
            </Container>
        );
    }
}

function isPath(str0) {
    if (typeof (str0) != 'string') return false;
    return (str0.startsWith('sha1://') || str0.startsWith('sha1dir://') || str0.startsWith('key://'));
}

FileView.propTypes = {
    basePath: PropTypes.string,
    file: PropTypes.object,
    onOpenPath: PropTypes.func
};