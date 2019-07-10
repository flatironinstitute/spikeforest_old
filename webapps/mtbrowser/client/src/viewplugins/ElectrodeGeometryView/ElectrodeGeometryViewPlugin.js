import React, { Component } from "react";
import { ElectrodeGeometryWidget } from "@spikeforestwidgets-js";

const axios = require('axios');

class ElectrodeGeometryView extends Component {
    constructor(props) {
        super(props);
        this.state = {
            locations: null,
            labels: null
        };
    }

    async componentDidMount() {
        await this.loadGeom();
    }

    async componentDidUpdate(prevProps) {
        if ((prevProps.path !== this.props.path )) {
            await this.loadGeom();
        }
    }

    async loadGeom() {
        let { locations, labels } = await load_geom_csv(this.props.path);
        this.setState({ locations, labels })
    }

    render() {
        if (!this.state.locations) {
            return <div></div>;
        }
        return <ElectrodeGeometryWidget
            locations={this.state.locations}
            labels={this.state.labels}
        />;
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
    let txt = await loadText(path, {});
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

async function loadText(path, opts) {
    let response;
    try {
        response = await axios.get(`/api/loadText?path=${encodeURIComponent(path)}`);
    }
    catch (err) {
        console.error(err);
        return null;
    }
    let rr = response.data;
    if (rr.success) {
        return rr.text;
    }
    else return null;
}

function baseName(str) {
    var base = new String(str).substring(str.lastIndexOf('/') + 1);
    return base;
}
