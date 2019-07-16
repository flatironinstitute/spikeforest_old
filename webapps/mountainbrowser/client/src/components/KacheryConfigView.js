import React, { Component } from 'react';
import { Paper, Table, TableBody, TableHead, TableRow, TableCell, Toolbar, Button, Input } from '@material-ui/core';
import { MdAdd } from 'react-icons/md';


const KacheryName = (props) => {
    const { connectionStatus, kacheryName } = props.kacheryInfo;
    if (connectionStatus === 'connected') {
        return <span style={{ color: 'darkgreen' }}>{kacheryName}</span>;
    }
    else if (connectionStatus === 'not_connected') {
        return <span style={{ color: 'darkred' }}>{kacheryName}</span>;
    }
    else {
        return <span>{kacheryName}</span>;
    }
}

const ConnectionStatus = (props) => {
    const { connectionStatus } = props.kacheryInfo;
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
    const { kacheryName } = props.kacheryInfo;
    const { onCheckConnection } = props;
    return <Button onClick={() => onCheckConnection(kacheryName)} title={`Check connection to ${kacheryName}`}>
        Check connection
    </Button>
}


const KacheryConnectionRow = (props) => {
    return (
        <TableRow>
            <TableCell><KacheryName {...props}></KacheryName></TableCell>
            <TableCell><ConnectionStatus {...props}></ConnectionStatus></TableCell>
            <TableCell><CheckButton {...props}></CheckButton></TableCell>
        </TableRow>
    );
}

class ConfigView extends Component {
    state = {
        addingKachery: false,
        kacheryInfos: []
    }
    componentDidMount() {
        this.updateKacheryInfos();
        this.timer = setInterval(() => { this.updateKacheryInfos() }, 1000);
    }

    componentWillUnmount() {
        clearInterval(this.timer);
        this.timer = null;
    }
    renderKacheryTable() {
        return (
            <Table>
                <TableHead>
                    <TableRow>
                        <TableCell>Kachery name</TableCell>
                        <TableCell>Connection status</TableCell>
                        <TableCell>Check connection</TableCell>
                    </TableRow>
                </TableHead>
                <TableBody>
                    {
                        this.state.kacheryInfos.map((kci, ii) => (
                            <KacheryConnectionRow key={ii} onCheckConnection={this.handleCheckConnection} kacheryInfo={kci} />
                        ))
                    }
                </TableBody>
            </Table>
        );
    }
    handleCheckConnection = (kacheryName) => {
        let kc = this.props.kacheryManager.connection(kacheryName);
        kc && kc.resetStatus();
        this.updateKacheryInfos();
    }
    handleAddKachery = () => {
        // this.props.kacheryManager.addConnection('spikeforest.public_abc');
        this.setState({
            addingKachery: true
        });
    }
    handleAddKacheryInputChanged = (evt) => {
    }

    handleAddKacheryInputKeyDown = (evt) => {
        if (evt.keyCode === 13) { // enter
            this.doAddKachery(evt.target.value);
        }
        else if (evt.keyCode === 27) { // escape
            this.setState({ addingKachery: false });
        }
    }
    updateKacheryInfos = () => {
        const { kacheryManager } = this.props;
        let kacheryInfos = kacheryManager.allConnections().map((kc) => (
            {
                kacheryName: kc.kacheryName,
                connectionStatus: kc.connectionStatus
            }
        ));
        this.setState({
            kacheryInfos: kacheryInfos
        });
    }
    doAddKachery = (name) => {
        this.props.kacheryManager.addConnection(name);
        this.updateKacheryInfos()
        this.setState({ addingKachery: false });
    }
    renderKacheryControlBar() {
        if (!this.state.addingKachery) {
            return (
                <Toolbar>
                    <Button onClick={this.handleAddKachery} title="Add new remote kachery database">
                        <MdAdd /> Add kachery
                    </Button>
                </Toolbar>
            )
        } else {
            return (
                <Toolbar>
                    <Input
                        autoFocus={true}
                        onChange={this.handleAddKacheryInputChanged}
                        onKeyDown={this.handleAddKacheryInputKeyDown}
                        placeholder="Name or URL of the remote kachery to add"
                        fullWidth={true}
                        type="text"
                    />
                </Toolbar>
            )
        }
    }
    render() {
        return (
            <Paper>
                <h3>Kachery configuration</h3>
                {this.renderKacheryControlBar()}
                {this.renderKacheryTable()}
            </Paper>
        )
    }
}

export default ConfigView;