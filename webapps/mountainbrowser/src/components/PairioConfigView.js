import React, { Component, Fragment } from 'react';
import { TableRow, Table, TableHead, TableCell, Paper, TableBody, Button } from '@material-ui/core';

const PairioUrl = (props) => {
    const { connectionStatus } = props;
    if (connectionStatus === 'connected') {
        return <span style={{ color: 'darkgreen' }}>{props.pairioUrl}</span>;
    }
    else if (connectionStatus === 'not_connected') {
        return <span style={{ color: 'darkred' }}>{props.pairioUrl}</span>;
    }
    else {
        return <span>{props.pairioUrl}</span>;
    }
}

const ConnectionStatus = (props) => {
    const { connectionStatus } = props;
    if (connectionStatus === 'connected') {
        return <span style={{ color: 'darkgreen' }}>Connected</span>;
    }
    else if (connectionStatus === 'not_connected') {
        return <span style={{ color: 'darkred' }}>Not connected</span>;
    }
    else {
        return <span>{connectionStatus}</span>;
    }
}

const CheckButton = (props) => {
    const { pairioUrl, onCheckConnection } = props;
    return <Button onClick={() => onCheckConnection()} title={`Check connection to ${pairioUrl}`}>
        Check connection
    </Button>
}


const PairioConnectionRow = (props) => {
    return (
        <TableRow>
            <TableCell><PairioUrl {...props}></PairioUrl></TableCell>
            <TableCell><ConnectionStatus {...props}></ConnectionStatus></TableCell>
            <TableCell><CheckButton {...props}></CheckButton></TableCell>
        </TableRow>
    );
}

class PairioConfigView extends Component {
    state = {
        connectionStatus: 'unknown',
        pairioUrl: 'https://pairio.org'
    }
    componentDidMount() {
        this.updatePairioInfo();
        this.timer = setInterval(() => { this.updatePairioInfo() }, 1000);
    }

    componentWillUnmount() {
        clearInterval(this.timer);
        this.timer = null;
    }
    updatePairioInfo() {
        this.setState({
            connectionStatus: this.props.kacheryManager.pairioConnectionStatus()
        });
    }
    handleCheckConnection() {
        console.info('todo');
    }
    renderPairioTable() {
        return (

            <Table>
                <TableHead>
                    <TableRow>
                        <TableCell>Pairio URL</TableCell>
                        <TableCell>Connection status</TableCell>
                        <TableCell>Check connection</TableCell>
                    </TableRow>
                </TableHead>
                <TableBody>
                    <PairioConnectionRow onCheckConnection={this.handleCheckConnection} {...this.state} />
                </TableBody>
            </Table>
        );
    }
    render() {
        return (
            <React.Fragment>
            <Paper>
                <h3>Pairio configuration</h3>
                {this.renderPairioTable()}
            </Paper>
            </React.Fragment>
        );
    }
}

export default PairioConfigView;