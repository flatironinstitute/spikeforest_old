import { hot } from 'react-hot-loader/root';
import React, { Component } from 'react';
import AppBar, { AppBarSpacer } from './AppBar';
import PathBar from './PathBar';
import Grid from '@material-ui/core/Grid';
import BrowserTree from './BrowserTree.js';
import ItemView from './ItemView.js';
import * as itemViewPlugins from "../itemviewplugins";
import ConfigView from './ConfigView';
import KacheryManager from './KacheryManager';

const PAGE_CONFIG = 'config';
const PAGE_MAIN = 'main';

const MainContainer = (props) => {
    return (
        <div style={{ margin: 25 }}>
            <Grid container spacing={3}>
                <Grid item xs={12} md={6} lg={5} xl={4}>
                    <BrowserTree
                        path={props.path}
                        onItemSelected={props.onItemSelected}
                        pathHistory={props.pathHistory}
                        onGotoHistory={props.onGotoHistory}
                    />
                </Grid>
                <Grid item xs={12} md={6} lg={7} xl={7}>
                    <ItemView
                        item={props.currentItem}
                        viewPlugins={Object.values(itemViewPlugins)}
                        onOpenPath={props.onOpenPath}
                    />
                </Grid>
            </Grid>
        </div>
    );
}

function timeout(ms) {
    return new Promise(resolve => setTimeout(resolve, ms));
}

class MainWindow extends Component {
    constructor(props) {
        super(props);
        this.state = {
            currentPageName: PAGE_MAIN,
            path: 'key://pairio/spikeforest/gallery',
            pathHistory: [],
            currentItem: null
        };

        this.kacheryManager = new KacheryManager;
        this.kacheryManager.addConnection('spikeforest.public');
        this.kacheryManager.addConnection('spikeforest.public_xxx');
    }

    async componentDidMount() {
        // wait a little bit before checking connection to give a nice effect
        await timeout(800);
        await this.startIterating();
    }

    startIterating = async () => {
        await this.kacheryManager.checkWaitingConnections();
        setTimeout(this.startIterating, 5000);
    }


    handleOpenPage = (pageName) => {
        this.setState({
            currentPageName: pageName
        });
    }

    handlePathChanged = (path) => {
        this.setState({
            path: path,
            pathHistory: [...this.state.pathHistory, this.state.path]
        });
    }

    handleBackButton = () => {
        let { pathHistory } = this.state;
        if (pathHistory.length === 0) return;
        let path0 = pathHistory.pop();

        this.setState({
            path: path0,
            pathHistory: pathHistory
        });
    }

    handleItemSelected = (item) => {
        this.setState({
            currentItem: item
        });
    }

    handleGotoHistory = (ind) => {
        this.setState({
            path: this.state.pathHistory[ind],
            pathHistory: this.state.pathHistory.slice(0, ind)
        })
    }

    render() {
        const appBar = (
            <AppBar
                onOpenConfig={() => { this.handleOpenPage(PAGE_CONFIG) }}
                onOpenMain={() => { this.handleOpenPage(PAGE_MAIN) }}
                kacheryManager={this.kacheryManager}
            />
        )
        const appBarSpacer = <AppBarSpacer />;
        const pathBar = (
            <PathBar
                path={this.state.path}
                pathHistory={this.state.pathHistory}
                onPathChanged={this.handlePathChanged}
                onBackButton={this.handleBackButton}
            />
        )
        const mainContainer = (
            <MainContainer
                path={this.state.path}
                onItemSelected={this.handleItemSelected}
                currentItem={this.state.currentItem}
                onOpenPath={this.handlePathChanged}
                pathHistory={this.state.pathHistory}
                onGotoHistory={this.handleGotoHistory}
            />
        );
        const configView = (
            <ConfigView kacheryManager={this.kacheryManager}/>
        )
        switch (this.state.currentPageName) {
            case PAGE_MAIN:
                return (
                    <React.Fragment>
                        {appBar}
                        {appBarSpacer}
                        {pathBar}
                        {mainContainer}
                    </React.Fragment>
                );
            case PAGE_CONFIG:
                return (
                    <React.Fragment>
                        {appBar}
                        {appBarSpacer}
                        {configView}
                        {/* <PathBar />
                        <MainContainer /> */}
                    </React.Fragment>
                );
        }
    }
}

export default hot(MainWindow);