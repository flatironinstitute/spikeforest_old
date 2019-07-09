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
        let { file } = this.props;
        let elements = [];
        if (this.props.viewPlugins) {
            for (let plugin of this.props.viewPlugins) {
                if (file.type === 'file') {
                    if ('getViewElementsForFile' in plugin) {
                        let elements0 = plugin.getViewElementsForFile(`sha1://${file.file.sha1}${file.path}`, {size: file.file.size});
                        elements.push(...elements0);
                    }
                }
                else if (file.type === 'folder') {
                    if ('getViewElementsForFolder' in plugin) {
                        let elements0 = plugin.getViewElementsForFolder(file.dir, {path: file.path});
                        elements.push(...elements0);
                    }
                }
            }
        }
        return elements;
    }

    render() {
        let { file } = this.props;
        if (!file) {
            return <div></div>
        }

        let viewPluginElements = this.getViewPluginElements();

        if (file.type === 'file') {
            return (
                <div>
                    <table className="table">
                        <tr>
                            <td>Path</td>
                            <td>{file.path}</td>
                        </tr>
                        <tr>
                            <td>SHA-1</td>
                            <td>{(file.file || {}).sha1}</td>
                        </tr>
                        <tr>
                            <td>Size</td>
                            <td>{(file.file || {}).size}</td>
                        </tr>
                    </table>
                    <span>
                        {viewPluginElements}
                    </span>
                </div>
            )
        }
        else if (file.type === 'folder') {
            return (
                <div>
                    <table className="table">
                        <tr>
                            <td>Path</td>
                            <td>{file.path}</td>
                        </tr>
                    </table>
                    <span>
                        {viewPluginElements}
                    </span>
                </div>
            )
        }
    }
}

FileView.propTypes = {
    basePath: PropTypes.string,
    file: PropTypes.object
};