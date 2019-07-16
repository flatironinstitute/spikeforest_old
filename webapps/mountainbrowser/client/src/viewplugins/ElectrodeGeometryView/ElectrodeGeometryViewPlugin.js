import React, { Component } from "react";
import { ElectrodeGeometryWidget } from "@spikeforestwidgets-js";

const MountainClient = require('@mountainclient-js').MountainClient;

class ElectrodeGeometryView extends Component {
    constructor(props) {
        super(props);
        this.state = {
            locations: null,
            labels: null,
            dimensions: null
        };
    }

    async componentDidMount() {
        this.setState({
            dimensions: {
                width: this.container.offsetWidth,
                height: this.container.offsetHeight,
            },
        });
        await this.loadGeom();
    }

    async componentDidUpdate(prevProps) {
        if ((prevProps.path !== this.props.path)) {
            await this.loadGeom();
        }
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
        /></div>;
    }

    render() {
        const { dimensions } = this.state;

        return (
            <div className="determiningDimensions" ref={el => (this.container = el)}>
                {dimensions && this.renderContent()}
            </div>
        );
    }
}

export default class ElectrodeGeometryViewPlugin {
    static getViewElementsForFile(path, opts) {
        if (baseName(path) === 'geom.csv') {
            return [<ElectrodeGeometryView
                path={path}
            />];
        }
        return [];
    }
    static getViewElementsForDir(dir, opts) {
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
            labels.push(Number(i) + 1);
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
