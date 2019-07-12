import React, { Component } from "react";
import Plot from 'react-plotly.js';
// import { UnitWaveformsWidget } from "@spikeforestwidgets-js";

const MountainClient = require('@mountainclient-js').MountainClient;

class UnitWaveformsWidget extends Component {
    constructor(props) {
        super(props);
        this.state = {
        };

        this.colorArr = [
            "#e6194B",
            "#bfef45",
            "#3cb44b",
            "#42d4f4",
            "#4363d8",
            "#911eb4",
            "#f032e6",
            "#ffe119"
        ];
    }

    async componentDidMount() {
    }

    async componentDidUpdate(prevProps) {
    }

    render() {
        if (!this.props.averageWaveform)
            return <div>No average waveform.</div>

        let W = this.props.averageWaveform;
        let numTimepoints = W[0].length;
        let numChannels = W.length;

        // Auto determine spacing
        let vals = [];
        for (let ch = 0; ch < W.length; ch++) {
            for (let t = 0; t < W[ch].length; t++) {
                vals.push(W[ch][t]);
            }
        }
        // Custom sort is needed to deal with annoying case of scientific notation for very small values
        vals.sort(function (a, b) {
            if (Number(a) < Number(b)) return -1;
            else if (Number(b) < Number(a)) return 1;
            else return 0;
        });
        let pctl_low = vals[Math.floor(vals.length * 0.01)];
        let pctl_high = vals[Math.floor(vals.length * 0.99)];
        let spacing = pctl_high - pctl_low;

        let channel_series = [];
        for (let ch = 0; ch < W.length; ch++) {
            let x = [];
            let y = [];
            let color = this.colorArr[ch % this.colorArr.length];
            for (let t = 0; t < W[ch].length; t++) {
                x.push(t);
                y.push(W[ch][t] - spacing * ch);
            }
            channel_series.push({
                x: x, y: y,
                color: color,
                type: 'scatter',
                mode: 'lines',
                hoverinfo: 'skip'
            })
        }

        return <Plot
            data={channel_series}
            layout={{
                width: '100%',
                height: '100%',
                title: '',
                showlegend: false,
                xaxis: {
                    autorange: false,
                    range: [0, numTimepoints - 1],
                    showgrid: false,
                    zeroline: false,
                    showline: false,
                    ticks: '',
                    showticklabels: false
                },
                yaxis: {
                    autorange: false,
                    range: [- numChannels * spacing, spacing],
                    showgrid: false,
                    zeroline: false,
                    showline: false,
                    ticks: '',
                    showticklabels: false
                },
                margin: {
                    l: 20, r: 20, b: 0, t: 0
                }
            }}
            config={(
                {
                    displayModeBar: false,
                    responsive: false
                }
            )}
        />
    }
}

class UnitWaveformsView extends Component {
    constructor(props) {
        super(props);
        this.state = {
            averageWaveform: null
        };
    }

    async componentDidMount() {
        await this.loadAverageWaveform();
    }

    async componentDidUpdate(prevProps) {
        if ((prevProps.path !== this.props.path)) {
            await this.loadAverageWaveform();
        }
    }

    async loadAverageWaveform() {
        let averageWaveform = await load_average_waveform(this.props.averageWaveformPath);
        this.setState({ averageWaveform })
    }

    render() {
        if (!this.state.averageWaveform) {
            return <div>Loading...</div>;
        }
        return <UnitWaveformsWidget
            averageWaveform={this.state.averageWaveform}
        />;
    }
}

export default class UnitWaveformsViewPlugin {
    static getViewComponentsForFile(path, opts) {
        if (baseName(path) === 'average_waveform.json') {
            return [{
                component: <UnitWaveformsView
                    averageWaveformPath={path}
                    key={path}
                />,
                size: 'small'
            }];
        }
        return [];
    }
    static getViewComponentsForDir(dir, opts) {
        return [];
    }
};

async function load_average_waveform(path) {
    let mt = new MountainClient();
    mt.configDownloadFrom(['spikeforest.public']);

    let obj = await mt.loadObject(path, {});
    if (!obj) return null;
    return obj['waveform'] || null;
}

// async function loadObject(path, opts) {
//     if (!path) {
//         if ((opts.key) && (opts.collection)) {
//             path = `key://pairio/${opts.collection}/~${hash_of_key(opts.key)}`;
//         }
//     }
//     let response;
//     try {
//         response = await axios.get(`/api/loadObject?path=${encodeURIComponent(path)}`);
//     }
//     catch (err) {
//         console.error(err);
//         console.error(`Problem loading object: ${path}`);
//         return null;
//     }
//     let rr = response.data;
//     if (rr.success) {
//         return rr.object;
//     }
//     else return null;
// }

function baseName(str) {
    var base = new String(str).substring(str.lastIndexOf('/') + 1);
    return base;
}
