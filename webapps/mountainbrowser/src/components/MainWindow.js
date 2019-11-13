import { hot } from 'react-hot-loader/root';
import React, { Component } from 'react';
import AppBar, { AppBarSpacer } from './AppBar';
import PathBar from './PathBar';
import Grid from '@material-ui/core/Grid';
import BrowserTree, { TreeData } from './BrowserTree.js';
import ItemView from './ItemView.js';
import * as itemViewPlugins from "../itemviewplugins";
import ConfigView from './ConfigView';
import KacheryManager from './KacheryManager';
import { Box } from '@material-ui/core';

const queryString = require('query-string');

const PAGE_CONFIG = 'config';
const PAGE_MAIN = 'main';

const MainContainer = (props) => {
    return (
        <div style={{ margin: 25 }}>
            <Grid container spacing={3}>
                <Grid item xs={12} md={6} lg={5} xl={4}>
                    <div className="main-container-column">
                        <div style={{ flexGrow: 1, overflow: 'auto', background: '#0f65bb1a' }}>
                            <BrowserTree
                                path={props.path}
                                treeData={props.treeData}
                                selectedNodePath={props.selectedNodePath}
                                onItemSelected={props.onItemSelected}
                                pathHistory={props.pathHistory}
                                onGotoHistory={props.onGotoHistory}
                                kacheryManager={props.kacheryManager}
                            />
                        </div>
                        <div
                            style={{ overflow: 'auto', height: 150, background: 'gray' }}
                        />
                    </div>
                </Grid>
                <Grid item xs={12} md={6} lg={7} xl={7}>
                    <div className="main-container-column">
                        {/* I think the key is important in order to reset the scrolling on the div when the item path changes */}
                        <div key={props.currentItem ? props.currentItem.path : ''} style={{ overflow: 'auto' }}>
                            <ItemView
                                item={props.currentItem}
                                viewPlugins={Object.values(itemViewPlugins)}
                                kacheryManager={props.kacheryManager}
                                onOpenPath={props.onOpenPath}
                                onSelectItem={props.onSelectItem}
                            />
                        </div>
                    </div>
                </Grid>
            </Grid>
        </div >
    );
}

function timeout(ms) {
    return new Promise(resolve => setTimeout(resolve, ms));
}

class MainWindow extends Component {
    constructor(props) {
        super(props);
        var q = queryString.parse(location.search);
        this.state = {
            currentPageName: PAGE_MAIN,
            path: q.path || 'key://pairio/spikeforest/gallery',
            // path: 'sha1dir://07c5564b32e6d015d8eb43f15f6f4c22cb4a7760',
            // path: 'sha1://c5ad0ae29162d170c751eb44be1772f70360f826/analysis.json',
            // path: q.path || 'key://pairio/spikeforest/test_franklab.json',
            // path: 'sha1dir://07c5564b32e6d015d8eb43f15f6f4c22cb4a7760/example_recordings/synth_magland_001',
            pathHistory: [],
            currentItem: null
        };

        this.kacheryManager = new KacheryManager;
        this.kacheryManager.setLocalStorageConfigKey('kachery_manager');
        this.kacheryManager.addSystemConnection('spikeforest.public', { enabledByDefault: true });

        this.treeData = new TreeData;
    }

    async componentDidMount() {
        // wait a little bit before checking connection to give a nice effect
        await timeout(800);
        await this.startIterating();
    }

    startIterating = async () => {
        await this.kacheryManager.checkWaitingConnections();
        this.kacheryManager.saveConfigToLocalStorage();
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
            currentItem: item,
            selectedNodePath: item ? item.path : null
        });
    }

    handleGotoHistory = (ind) => {
        this.setState({
            path: this.state.pathHistory[ind],
            pathHistory: this.state.pathHistory.slice(0, ind)
        })
    }

    handleSelectItem = (path) => {
        this.setState({
            selectedNodePath: path,
            currentItem: this.treeData.findNodeByPath(path)
        });
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
                selectedNodePath={this.state.selectedNodePath}
                onOpenPath={this.handlePathChanged}
                onSelectItem={this.handleSelectItem}
                pathHistory={this.state.pathHistory}
                onGotoHistory={this.handleGotoHistory}
                kacheryManager={this.kacheryManager}
                treeData={this.treeData}
            />
        );
        const configView = (
            <ConfigView kacheryManager={this.kacheryManager} />
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
                    </React.Fragment>
                );
        }
    }
}

export default hot(MainWindow);