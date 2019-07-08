import React, { Component } from 'react';
import PropTypes from 'prop-types';

const axios = require("axios");
import Highlight from "react-highlight.js";

export default class FileView extends Component {
    constructor(props) {
        super(props);
        this.state = {
            fileContent: null,
            fileContentStatus: 'not-loading'
        };
    }

    async componentDidMount() {
        await this.updateContent();
    }

    async componentDidUpdate(prevProps) {
        if (prevProps.file !== this.props.file) {
            await this.updateContent();
        }
    }

    async updateContent() {
        let { file } = this.props;
        this.setState({
            fileContentStatus: 'not-loading',
            fileContent: null
        });
        if ((file) && (file.type === 'file')) {
            if (file.file.size < 10000) {
                let path0 = `sha1://${file.file.sha1}`;
                console.log(path0);
                this.setState({
                    fileContentStatus: 'loading'
                });
                let txt0 = await loadText(path0);
                if (txt0) {
                    this.setState({
                        fileContentStatus: 'loaded',
                        fileContent: txt0
                    });
                }
                else {
                    this.setState({
                        fileContentStatus: 'failed'
                    });
                }
            }
        }
    }

    getContentElement() {
        if (this.state.fileContentStatus === 'loading') {
            return <div>Loading content...</div>;
        }
        else if (this.state.fileContentStatus === 'failed') {
            return <div>Failed to load content</div>;
        }
        else if (this.state.fileContentStatus === 'loaded') {
            return <Highlight language="javascript">
                {this.state.fileContent}
            </Highlight>
        }
        else {
            return <div></div>;
        }
    }

    render() {
        let { file } = this.props;
        if (!file) {
            return <div></div>
        }

        let content = this.getContentElement();

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
                    {content}
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
                </div>
            )
        }
    }
}

async function loadText(path, opts) {
    let response;
    try {
        response = await axios.get(`/api/loadText?path=${encodeURIComponent(path)}`);
    }
    catch (err) {
        console.error(err);
        return null;
    }
    let rr = response.data;
    if (rr.success) {
        return rr.text;
    }
    else return null;
}

FileView.propTypes = {
    basePath: PropTypes.string,
    file: PropTypes.object
};