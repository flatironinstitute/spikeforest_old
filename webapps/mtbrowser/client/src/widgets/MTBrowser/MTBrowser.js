import React, { Component } from "react";
import { Container, Row, Col } from 'react-bootstrap';
import Tree from "./Tree"
import FileView from "./FileView"
import PropTypes from "prop-types";

const axios = require("axios");

export class MTBrowser extends Component {
    constructor(props) {
        super(props);
        this.state = {
            status: `Loading: ${this.props.path}`,
            selectedFile: null
        };
    }

    async componentDidMount() {
        let X = await loadDirectory(this.props.path, {});
        if (X) {
            this.setState({
                status: `loaded`,
                data: X
            });
        }
        else {
            this.setState({
                status: `Unable to load: ${this.props.path}`
            });
        }
    }

    onSelect = (file) => {
        this.setState({
            selectedFile: file
        });
    }

    render() {
        if (this.state.status === 'loaded') {
            return <Container fluid={true}>
                <Row noGutters={true}>
                    <Col md={6}>
                        <Tree data={this.state.data} onSelect={(node) => { this.onSelect(node); }}></Tree>
                    </Col>
                    <Col md={6}>
                        <FileView file={this.state.selectedFile} basePath={this.props.path}></FileView>
                    </Col>
                </Row>
                
            </Container>
        }
        else if (this.state.status === 'loading') {
            return <div>Loading...</div>
        }
        else {
            return <div>{this.state.status}</div>
        }
    }
}

MTBrowser.propTypes = {
    path: PropTypes.string
}

async function loadDirectory(path) {
    let vals = path.split('/');
    if (vals[0] !== 'sha1dir:') {
        return null;
    }
    let X = await loadObject(`sha1://${vals[2]}`);
    if (!X) return;
    for (let i=3; i < vals.length; i++) {
        if (vals[i]) {
            if ((X.dirs) && (vals[i] in X.dirs)) {
                X = X.dirs[vals[i]];
            }
            else {
                return null;
            }
        }
    }
    return X;
}

async function loadObject(path, opts) {
    if (!path) {
        if ((opts.key) && (opts.collection)) {
            path = `key://pairio/${opts.collection}/~${hash_of_key(opts.key)}`;
        }
    }
    let response;
    try {
        response = await axios.get(`/api/loadObject?path=${encodeURIComponent(path)}`);
    }
    catch (err) {
        return null;
    }
    let rr = response.data;
    if (rr.success) {
        return rr.object;
    }
    else return null;
}

function example_data() {
    return {
        "files": {
            "index.js": {
                "size": 310,
                "sha1": "2dd6248bcd0ba0c4fc59f58085abbd47e5d1f17e"
            }
        },
        "dirs": {
            "widgets": {
                "files": {
                    "index.js": {
                        "size": 50,
                        "sha1": "82073d94fa7ff3ed7923287d36b9e4e0f6671bc0"
                    }
                },
                "dirs": {
                    "MTBrowser": {
                        "files": {
                            "Tree.js": {
                                "size": 2076,
                                "sha1": "f7c49b972b5bc3a1cc0cdf74fdbe14223438519f"
                            },
                            "TreeNode.js": {
                                "size": 2073,
                                "sha1": "ce3f22f3e105952ddb87bfd5daa0315d740ba19b"
                            },
                            "MTBrowser.js": {
                                "size": 488,
                                "sha1": "e98a6c46428346a94fecdba18c2f99c97870f03f"
                            }
                        },
                        "dirs": {}
                    }
                }
            }
        }
    };
}