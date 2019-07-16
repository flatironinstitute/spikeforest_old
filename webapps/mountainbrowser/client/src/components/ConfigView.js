import React, { Component } from 'react';
import KacheryConfigView from './KacheryConfigView';
import PairioConfigView from './PairioConfigView';
import { Grid } from '@material-ui/core';
import SpacerComponent from './SpacerComponent';

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
                </Grid>
                <Grid item xs={12} md={6} lg={7} xl={7}>
                </Grid>
            </Grid>
        )
    }
}

export default ConfigView;