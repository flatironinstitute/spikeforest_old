import React, { Component } from 'react';
import KacheryConfigView from './KacheryConfigView';
import PairioConfigView from './PairioConfigView';
import LocalStorageConfigView from './LocalStorageConfigView';
import ElectronConfigView from './ElectronConfigView';
import { Grid, Paper, Button } from '@material-ui/core';
import SpacerComponent from './SpacerComponent';
import developmentTest from './developmentTest';

class ConfigView extends Component {
    state = {
    }
    render() {
        return (
            <Grid container spacing={3}>
                <Grid item xs={12} md={6} lg={5} xl={4}>
                    <KacheryConfigView {...this.props} />
                    <SpacerComponent height={60} />
                    <PairioConfigView {...this.props} />
                    <SpacerComponent height={60} />
                    <LocalStorageConfigView {...this.props} />
                    <SpacerComponent height={60} />
                    <ElectronConfigView {...this.props} />
                    <SpacerComponent height={60} />
                    <Paper>
                        <Button onClick={() => {developmentTest();}}>
                            Execute development test
                        </Button>
                    </Paper>
                </Grid>
                <Grid item xs={12} md={6} lg={7} xl={7}>
                </Grid>
            </Grid>
        )
    }
}

export default ConfigView;