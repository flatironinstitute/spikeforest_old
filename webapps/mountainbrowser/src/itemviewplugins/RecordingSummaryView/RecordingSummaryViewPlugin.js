import React, { Component } from "react";
import { ElectrodeGeometryView } from "../ElectrodeGeometryView/ElectrodeGeometryViewPlugin";
import { Button } from "@material-ui/core";
import UnitsTable from "./UnitsTable";
import UnitDetailWidget from "./UnitDetailWidget";
import AutocorrelogramsView from "../spikeforestanalysis/AutocorrelogramsView";
import TimeseriesView from "../spikeforestanalysis/TimeseriesView";
import ReactComponentPythonCompanion from "../ReactComponentPythonCompanion";
import UnitsView from "./UnitsView";
import ButtonOpen from "./ButtonOpen";
import EventAmplitudesView from "./EventAmplitudesView";

export class RecordingSummaryView extends Component {
    constructor(props) {
        super(props);
        this.state = {
            locations: null,
            labels: null,
            params: null,
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
                params: null
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
        const { locations } = this.state;
        if (!locations) {
            return <div></div>;
        }
        return (
            <div>
                <table className="table">
                    <tbody>
                        <tr><td>Recording</td><td>{this.props.recordingPath}</td></tr>
                        <tr><td>Sampling freq (Hz)</td><td>{this.state.params ? this.state.params.samplerate : '...'}</td></tr>
                        <tr><td>Num. channels</td><td>{this.state.locations ? this.state.locations.length : '...'}</td></tr>
                    </tbody>
                </table>
                <ButtonOpen label='Timeseries'>
                    <TimeseriesView
                        kacheryManager={this.props.kacheryManager}
                        recordingPath={this.props.recordingPath}
                    />
                </ButtonOpen>
                <ButtonOpen label='Electrode geometry'>
                    <ElectrodeGeometryView
                        path={this.props.geomPath}
                        kacheryManager={this.props.kacheryManager}
                    />
                </ButtonOpen>
                <ButtonOpen label='Units'>
                    <UnitsView
                        recordingPath={this.props.recordingPath}
                        firingsPath={`${this.props.recordingPath}/firings_true.mda`}
                        kacheryManager={this.props.kacheryManager}
                        onUnitSelected={(unitInfo) => {this.setState({selectedUnitId: unitInfo.unit_id})}}
                    />
                </ButtonOpen>
                <ButtonOpen label='Autocorrelograms'>
                    <AutocorrelogramsView
                        kacheryManager={this.props.kacheryManager}
                        samplerate={(this.state.params || {}).samplerate}
                        firingsPath={this.props.recordingPath + '/firings_true.mda'}
                    />
                </ButtonOpen>
                <ButtonOpen label='Event amplitudes'>
                    <EventAmplitudesView
                        kacheryManager={this.props.kacheryManager}
                        recordingPath={this.props.recordingPath}
                        firingsPath={this.props.recordingPath + '/firings_true.mda'}
                        unitIds={this.state.selectedUnitId ? [this.state.selectedUnitId] : []}
                    />
                </ButtonOpen>
                {/* {
                    this.state.selectedUnitId ? (
                        <ButtonOpen label='Selected unit details'>
                            <UnitDetailWidget
                                recordingPath={this.props.recordingPath}
                                firingsPath={this.props.recordingPath + '/firings.mda'}
                                kacheryManager={this.props.kacheryManager}
                                unitId={this.state.selectedUnitId}
                            />
                        </ButtonOpen>
                    ) : (<span></span>)
                } */}

            </div>
        )
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

