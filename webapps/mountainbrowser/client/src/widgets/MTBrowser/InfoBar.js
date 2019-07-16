import React, { Component } from 'react';
import PropTypes from 'prop-types';
import { FaCircle, FaCog } from 'react-icons/fa';
import AppBar from '@material-ui/core/AppBar';
import Toolbar from '@material-ui/core/Toolbar';

import styled from 'styled-components';
import { Typography, IconButton, Button } from '@material-ui/core';

class KacheryStatusIndicator extends Component {
    constructor(props) {
        super(props);
        this.state = {
        };
    }

    componentDidMount() {
    }


    render() {
        const kc = this.props.kacheryConnection;
        let color_for_status = {
            connected: 'lightgreen',
            disconnected: 'darkred'
        };
        const color = color_for_status[kc.connectionStatus] || 'gray';
        return <IconButton size="small" style={{color: color}} title={`kachery: ${kc.name} (${kc.connectionStatus})`}>
                <FaCircle />
            </IconButton>;
    }
}

class KacheryCogButton extends Component {    
    render() {
        const color = 'lightgray';
        return <IconButton
            style={{color: color}}
            title="Configure kachery connections"
            onClick={() => {this.props.onClick && this.props.onClick()}}
        >
            <FaCog />
        </IconButton>
    }
}


export default class InfoBar extends Component {
    constructor(props) {
        super(props);
        this.state = {
        };
    }

    componentDidMount() {
    }

    handleKacheryCogClick = () => {
    }

    handleTitleClick = () => {
    }

    render() {
        return <AppBar>
            <Toolbar variant="dense" disableGutters={false}>
                {/* <Button onClick={this.handleTitleClick}> */}
                <Typography
                    variant="inherit"
                    color='inherit'
                    style={{
                        cursor: 'pointer'
                    }}
                    onClick={this.handleTitleClick}
                >
                    MountainBrowser
                </Typography>
                {/* </Button> */}
                <div style={{ width: '50px' }} />
                <KacheryCogButton onClick={this.handleKacheryCogClick} />
                {this.props.kacheryManager.map((kc) => (
                    <KacheryStatusIndicator kacheryConnection={kc} key={kc.name} />
                ))}
            </Toolbar>
        </AppBar>
    }
}
