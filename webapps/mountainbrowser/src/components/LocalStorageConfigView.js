import React, { Component } from 'react';
import { TableRow, Table, TableHead, TableCell, Paper, TableBody, Button, FormControl, Checkbox, FormControlLabel, FormLabel } from '@material-ui/core';

class LocalStorageConfigView extends Component {
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
    handleClearLocalStorageCache = () => {
        const { kacheryManager } = this.props;
        kacheryManager.localStorageCacheManager().clear();
        this.forceRerender();
    }
    render() {
        const { kacheryManager } = this.props;
        return (
            <Paper>
                <h3>Local storage configuration</h3>
                <FormControl>
                    <FormControlLabel
                        control={<Checkbox checked={kacheryManager.localStorageCacheEnabled()} onChange={(evt, val) => { kacheryManager.setLocalStorageCacheEnabled(val); this.forceRerender(); }} />}
                        label="Use local storage cache"
                    />
                    <FormLabel>
                        {`Space used (KB): ${Math.round(kacheryManager.localStorageCacheManager().totalBytesUsed() / 1024)}`}
                    </FormLabel>
                    <Button color={'primary'} onClick={this.handleClearLocalStorageCache}>
                        Clear local storage cache
                    </Button>
                    <FormLabel>
                        {window.electron ? 'has electron' : 'does not have electron'}
                    </FormLabel>
                </FormControl>
            </Paper>
        );
    }
}

export default LocalStorageConfigView;