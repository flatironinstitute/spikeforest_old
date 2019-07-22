import React, { Component } from 'react';
import { AppBar as MaterialAppBar, Typography, Toolbar, IconButton } from '@material-ui/core';
import { FaCog } from "react-icons/fa";
import KacheryStatusIndicator from './KacheryStatusIndicator';
import SpacerComponent from './SpacerComponent';

export const AppBarSpacer = () => {
    return (
        // Needs to match the toolbar of AppBar for purpose of spacing
        <Toolbar variant="dense" />
    )
}

const TitleComponent = (props) => {
    return <Typography
        variant="inherit"
        color='inherit'
        style={{
            cursor: 'pointer'
        }}
        onClick={props.onClick}
    >
        MountainBrowser
    </Typography>
}

const KacheryCogButton = (props) => {
    const color = 'lightgray';
    return <IconButton
        style={{ color: color }}
        title="Configure kachery connections"
        onClick={() => { props.onClick && props.onClick() }}
    >
        <FaCog />
    </IconButton>
}

class AppBar extends Component {
    state = {
        kacheryInfos: []
    }

    componentDidMount() {
        this.updateKacheryInfos();
        this.timer = setInterval(() => {this.updateKacheryInfos()}, 1000);
    }

    componentWillUnmount() {
        clearInterval(this.timer);
        this.timer = null;
    }

    updateKacheryInfos = () => {
        const { kacheryManager } = this.props;
        let kacheryInfos = kacheryManager.allConnections().filter((kc) => (
            kc.enabled === true
        )).map((kc) => (
            {
                kacheryName: kc.kacheryName,
                connectionStatus: kc.connectionStatus
            }
        ));
        this.setState({
            kacheryInfos: kacheryInfos
        });
    }

    handleKacheryCogClick = () => {
        this.props.onOpenConfig && this.props.onOpenConfig();
    }

    handleKacheryIndicatorClick = (kacheryName) => {
        let kc = this.props.kacheryManager.connection(kacheryName);
        kc && kc.resetStatus();
        this.props.onOpenConfig && this.props.onOpenConfig();
    }

    handleTitleClick = () => {
        this.props.onOpenMain && this.props.onOpenMain();
    }

    render() {

        return (
            <MaterialAppBar>
                <Toolbar variant="dense" disableGutters={false}>
                    <TitleComponent onClick={this.handleTitleClick} />
                    <SpacerComponent width={50} />
                    <KacheryCogButton onClick={this.handleKacheryCogClick} />
                    {this.state.kacheryInfos.map((kci, ii) => (
                        <KacheryStatusIndicator
                            kacheryName={kci.kacheryName}
                            connectionStatus={kci.connectionStatus}
                            key={ii}
                            onClick={this.handleKacheryIndicatorClick}
                        />
                    ))}
                </Toolbar>
            </MaterialAppBar>
        );
    }
}

export default AppBar;