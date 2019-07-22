import React, { Component } from 'react';
import { TableRow, Table, TableHead, TableCell, Paper, TableBody, Button, FormControl, Checkbox, FormControlLabel, FormLabel } from '@material-ui/core';

class ElectronConfigView extends Component {
    state = {
        rerenderCode: 0
    }
    componentDidMount() {

    }

    componentWillUnmount() {
    }

    forceRerender() {
        this.setState({
            rerenderCode: this.state.rerenderCode + 1
        });
    }
    render() {
        const { kacheryManager } = this.props;
        return (
            <Paper>
                <h3>Electron configuration</h3>
                <FormControl>
                    <FormLabel>
                        {window.using_electron ? 'Using electron' : 'Not using electron'}
                    </FormLabel>
                    <FormControlLabel
                        control={<Checkbox checked={kacheryManager.electronFileSystemAccessEnabled()} onChange={(evt, val) => { kacheryManager.setElectronFileSystemAccessEnabled(val); this.forceRerender(); }} />}
                        label="Allow file system access"
                        disabled={window.using_electron ? false : true}
                    />
                </FormControl>
            </Paper>
        );
    }
}

export default ElectronConfigView;