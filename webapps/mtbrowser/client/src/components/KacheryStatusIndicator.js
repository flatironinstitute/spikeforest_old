import React, { Component } from 'react';
import { IconButton } from '@material-ui/core';
import { FaCircle } from 'react-icons/fa';

class KacheryStatusIndicator extends Component {
    state = {}
    render() {
        const { kacheryName, connectionStatus } = this.props;
        let color_for_status = {
            connected: 'lightgreen',
            not_connected: 'darkred'
        };
        const color = color_for_status[connectionStatus] || 'gray';
        return (
            <IconButton size="small" style={{ color: color }} onClick={() => this.props.onClick(kacheryName)} title={`kachery: ${kacheryName} (${connectionStatus})`}>
                <FaCircle />
            </IconButton>
        );
    }
}

export default KacheryStatusIndicator;