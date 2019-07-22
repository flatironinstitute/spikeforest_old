import React, { Component } from "react";
import { ElectrodeGeometryView } from "../ElectrodeGeometryView/ElectrodeGeometryViewPlugin";
import { Button } from "@material-ui/core";
import ComputeRecordingInfoJob from "./ComputeRecordingInfo.json";
import ComputeUnitsInfoJob from "./ComputeUnitsInfo.json";
import UnitsTable from "./UnitsTable";
import UnitDetailWidget from "./UnitDetailWidget";

class ComputeWidget extends Component {
    constructor(props) {
        super(props);
        this.state = {
            status: 'pending',
            error: null,
            result: null,
            output: null
        };
    }
    componentDidUpdate(prevProps) {
        if (prevProps.recordingPath !== this.props.recordingPath) {
            this.setState({
                status: 'pending'
            });
        }
    }
    compute = async () => {
        this.setState({ status: 'running' });
        let result_recording_info = await window.executeJob(
            ComputeRecordingInfoJob,
            { recording_dir: this.props.recordingPath },
            { download_from: 'spikeforest.public' }
        )
        if (result_recording_info.retcode !== 0) {
            let txt = await this.props.kacheryManager.loadText(result.console_out);
            console.error(txt);
            this.setState({ status: 'error', error: 'Error running job ComputeRecordingInfo.' });
            return;
        }

        this.setState({ status: 'running' });
        let result_units_info = await window.executeJob(
            ComputeUnitsInfoJob,
            { recording_dir: this.props.recordingPath, firings: this.props.recordingPath + '/firings_true.mda' },
            { download_from: 'spikeforest.public' }
        )
        if (result_units_info.retcode !== 0) {
            let txt = await this.props.kacheryManager.loadText(result.console_out);
            console.error(txt);
            this.setState({ status: 'error', error: 'Error running job ComputeUnitsInfo.' });
            return;
        }

        let output = {
            recording_info: await this.props.kacheryManager.loadObject(result_recording_info.outputs.json_out),
            units_info: await this.props.kacheryManager.loadObject(result_units_info.outputs.json_out)
        };
        this.setState({
            status: 'finished',
            output: output
        });
        this.props.onFinished && this.props.onFinished(output);
    }
    render() {
        const { status } = this.state;
        if (status === 'pending') {
            return (
                <Button onClick={this.compute}>Compute summary info</Button>
            )
        }
        else if (status === 'running') {
            return (
                <div>Running...</div>
            );
        }
        else if (status === 'finished') {
            return (
                <div>
                    <span>Computation finished.</span>
                    {/* <span><pre>{JSON.stringify(this.state.output, null, 4)}</pre></span> */}
                </div>
            );
        }
        else if (status === 'error') {
            return (
                <div>Error: {this.state.error}</div>
            );
        }
        else {
            return (
                <div>Unexpected status: {status}</div>
            );
        }
    }
}

class RecordingSummaryView extends Component {
    constructor(props) {
        super(props);
        this.state = {
            locations: null,
            labels: null,
            params: null,
            output: null,
            selectedUnitId: null
        };
    }

    async componentDidMount() {
        await this.update();
    }

    async componentDidUpdate(prevProps) {
        if (prevProps !== this.props) {
            this.setState({
                locations: null,
                labels: null,
                params: null,
                output: null
            })
            await this.update();
        }
    }

    async update() {
        await this.loadGeom();
        await this.loadParams();
    }

    async loadGeom() {
        this.setState({ locations: null, labels: null });
        let geomTxt = await this.props.kacheryManager.loadText(this.props.geomPath);
        let locations = load_geom_csv(geomTxt);
        if (!locations) return { locations: null, labels: null };
        let labels = [];
        for (let i in locations) {
            labels.push(Number(i) + 1);
        }
        this.setState({ locations, labels })
    }

    async loadParams() {
        this.setState({ params: null });

        let params = await (this.props.kacheryManager.loadObject(this.props.paramsPath));
        this.setState({ params: params });
    }

    handleUnitSelected = (unitInfo) => {
        this.setState({
            selectedUnitId: unitInfo ? unitInfo.unit_id : null
        });
    }

    render() {
        const { output, locations } = this.state;
        if (!locations) {
            return <div></div>;
        }
        return <div>
            <ComputeWidget
                recordingPath={this.props.recordingPath}
                kacheryManager={this.props.kacheryManager}
                onFinished={(output) => this.setState({ output: output })}
            />
            <table className="table">
                <tbody>
                    <tr><td>Sampling freq (Hz)</td><td>{this.state.params ? this.state.params.samplerate : '...'}</td></tr>
                    <tr><td>Num. channels</td><td>{this.state.locations ? this.state.locations.length : '...'}</td></tr>
                    <tr><td>Duration (sec)</td><td>{output ? output.recording_info.duration_sec : '.'}</td></tr>
                </tbody>
            </table>
            <ElectrodeGeometryView
                path={this.props.geomPath}
                kacheryManager={this.props.kacheryManager}
            />
            {
                (output && output.units_info) ?
                    (
                        <div style={{ overflow: 'auto', height: 200 }}>
                            <UnitsTable
                                unitsInfo={output.units_info}
                                onUnitSelected={this.handleUnitSelected}
                            />
                        </div>
                    ) : <span></span>

            }
            {
                this.state.selectedUnitId ? (
                    <UnitDetailWidget
                        recordingPath={this.props.recordingPath}
                        firingsPath={this.props.recordingPath + '/firings.mda'}
                        kacheryManager={this.props.kacheryManager}
                        unitId={this.state.selectedUnitId}
                    />
                ) : (<span></span>)
            }
        </div>;
    }
}

export default class RecordingSummaryViewPlugin {
    static getViewComponentsForFile(path, opts) {
        return [];
    }
    static getViewComponentsForDir(path, dir, opts) {
        if (('geom.csv' in dir.files) && ('params.json' in dir.files)) {
            return [{
                component: <RecordingSummaryView
                    geomPath={`sha1://${dir.files['geom.csv'].sha1}/geom.csv`}
                    paramsPath={`sha1://${dir.files['params.json'].sha1}/params.json`}
                    recordingPath={path}
                    kacheryManager={opts.kacheryManager}
                />,
                size: 'large'
            }];
        }
        return [];
    }
};

function load_geom_csv(txt) {
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
    return locations
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

// async function loadObject(path, opts) {
//     opts = opts || {};
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

