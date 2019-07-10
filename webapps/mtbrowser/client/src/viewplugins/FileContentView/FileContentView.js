import React, { Component } from "react";

const axios = require("axios");
import Highlight from "react-highlight.js";

export default class FileContentView extends Component {
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
        if ((prevProps.path !== this.props.path) || (prevProps.size !== this.props.size)) {
            await this.updateContent();
        }
    }

    async updateContent() {
        let { path, size } = this.props;
        this.setState({
            fileContentStatus: 'not-loading',
            fileContent: null
        });
        if (size < 10000) {
            this.setState({
                fileContentStatus: 'loading'
            });
            let txt0 = await loadText(path);
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

    getContentElement() {
        if (this.state.fileContentStatus === 'loading') {
            return <div>Loading content...</div>;
        }
        else if (this.state.fileContentStatus === 'failed') {
            return <div>Failed to load content</div>;
        }
        else if (this.state.fileContentStatus === 'loaded') {
            return <Highlight language={determineLanguageFromFilePath(this.props.path)}>
                {this.state.fileContent}
            </Highlight>
        }
        else {
            return <div></div>;
        }
    }

    render() {
        return <div style={{overflow: 'auto', height: '300px'}}>
            {this.getContentElement()}
        </div>
    }
}

function determineLanguageFromFilePath(path) {
    let map = {
        '.js': 'javascript',
        '.json': 'json',
        '.py': 'python',
        '.html': 'html',
        '.md': 'markdown'
    };
    for (let key in map) {
        if (path.endsWith(key)) {
            return map[key];
        }
    }
    return '';
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
