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
        let txt0 = await this.kacheryManager.loadText(this.props.path);
        let locations = load_geom_csv(txt0);
        let labels = [];
        for (let i in locations) {
            labels.push(Number(i) + 1);
        }
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
                kacheryManager={opts.kacheryManager}
            />];
        }
        return [];
    }
    static getViewElementsForDir(dir, opts) {
        return [];
    }
};

function load_geom_csv(txt) {
    if (!txt) return null;
    let locations = [];
    var list = txt.split('\n');
    for (var i in list) {
        if (list[i].trim()) {
            var vals = list[i].trim().split(',');
            for (var j in vals) {
                vals[j] = Number(vals[j]);
            }
            while (vals.length < 2) vals.push(0);
            locations.push(vals);
        }
    }
    return locations;
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
