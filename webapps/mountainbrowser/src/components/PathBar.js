import React, { Component } from 'react';
import { Toolbar, IconButton, Button } from "@material-ui/core";
import { FaArrowLeft } from "react-icons/fa";
import { MdRefresh } from "react-icons/md";

class PathBar extends Component {
    state = {
        inputPath: this.props.path || ''
    }

    componentDidMount() {
        this.setState({
            inputPath: this.props.path
        });
    }

    componentDidUpdate(prevProps) {
        if (prevProps.path !== this.props.path) {
            this.setState({
                inputPath: this.props.path
            });
        };
    }

    handlePathInputChanged = (evt) => {
        this.setState({
            inputPath: evt.target.value
        });
    }

    handlePathInputKeyDown = (evt) => {
        if (evt.keyCode === 13) {
            this.handleUpdate();
        }
    }

    handleBackButton = () => {
        this.props.onBackButton && this.props.onBackButton();
    }

    handleUpdate = () => {
        this.setNewPath(this.state.inputPath);
    }

    setNewPath = (path) => {
        if (path === this.props.path) {
            return;
        }

        // var q = queryString.parse(location.search);
        // q.path = path;

        this.props.onPathChanged && this.props.onPathChanged(path);
    }

    render() {
        const inputLength = Math.ceil(Math.max(50, this.state.inputPath.length) / 10) * 10;
        return (
            <Toolbar>
                <IconButton onClick={this.handleBackButton} disableRipple={true}
                    disabled={(this.props.pathHistory.length === 0)}
                >
                    <FaArrowLeft />
                </IconButton>
                <input
                    autoComplete="off" autoCorrect="off" autoCapitalize="off" spellCheck="off"
                    type="text"
                    className="form-control"
                    placeholder="Enter path (sha1dir://, sha1://, key://, etc.)"
                    onChange={this.handlePathInputChanged}
                    onKeyDown={this.handlePathInputKeyDown}
                    style={{ maxWidth: `${inputLength}ch` }}
                    value={this.state.inputPath}
                />
                <IconButton
                    onClick={this.handleUpdate}
                    disabled={this.props.path === this.state.inputPath}
                >
                    <MdRefresh />
                </IconButton>
            </Toolbar>
        );
    }
}

export default PathBar;