import React, { Component } from "react";
import { ElectrodeGeometryWidget } from "@spikeforestwidgets-js";

const MountainClient = require('@mountainclient-js').MountainClient;

export class ElectrodeGeometryView extends Component {
    constructor(props) {
        super(props);
        this.state = {
            locations: null,
            labels: null,
            width: null
        };
    }

    async componentDidMount() {
        this.updateDimensions();
        window.addEventListener("resize", this.resetWidth);
        await this.loadGeom();
    }

    componentWillUnmount() {
        window.removeEventListener("resize", this.resetWidth);
    }

    resetWidth = () => {
        this.setState({
            width: null
        });
    }

    async componentDidUpdate(prevProps, prevState) {
        if (!this.state.width) {
            this.updateDimensions();
        }
        if ((prevProps.path !== this.props.path)) {
            await this.loadGeom();
        }
    }

    updateDimensions() {
        this.setState({
            width: this.container.offsetWidth // see render()
        });
    }

    async loadGeom() {
        let { locations, labels } = await load_geom_csv(this.props.path);
        this.setState({ locations, labels })
    }

    renderContent() {
        if (!this.state.locations) {
            return <div></div>;
        }
        return <div><ElectrodeGeometryWidget
            locations={this.state.locations}
            labels={this.state.labels}
            width={this.state.width}
            height={null}
        /></div>;
    }

    render() {
        const { width } = this.state;

        return (
            <div className="determiningWidth" ref={el => (this.container = el)}>
                {width && this.renderContent()}
            </div>
        );
    }
}

export default class ElectrodeGeometryViewPlugin {
    static getViewComponentsForFile(path, opts) {
        if (baseName(path) === 'geom.csv') {
            return [{
                component: <ElectrodeGeometryView path={path} />,
                size: 'large'
            }];
        }
        return [];
    }
    static getViewComponentsForDir(dir, opts) {
        return [];
    }
};

async function load_geom_csv(path) {
    let mt = new MountainClient();
    mt.configDownloadFrom(['spikeforest.public']);
    
    let txt = await mt.loadText(path, {});
    if (!txt) return null;
    let locations = [];
    let labels = [];
    var list = txt.split('\n');
    for (var i in list) {
        if (list[i].trim()) {
            var vals = list[i].trim().split(',');
            for (var j in vals) {
                vals[j] = Number(vals[j]);
            }
            while (vals.length < 2) vals.push(0);
            locations.push(vals);
            labels.push(Number(i)+1);
        }
    }
    return {
        locations,
        labels
    };
}

// async function loadText(path, opts) {
//     let response;
//     try {
//         response = await axios.get(`/api/loadText?path=${encodeURIComponent(path)}`);
//     }
//     catch (err) {
//         console.error(err);
//         return null;
//     }
//     let rr = response.data;
//     if (rr.success) {
//         return rr.text;
//     }
//     else return null;
// }

function baseName(str) {
    var base = new String(str).substring(str.lastIndexOf('/') + 1);
    return base;
}
