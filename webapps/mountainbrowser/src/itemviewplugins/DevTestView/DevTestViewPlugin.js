import React, { Component } from "react";
import { Button } from "@material-ui/core";
import repeat_text from "./repeat_text.json";

export class DevTestView extends Component {
    constructor(props) {
        super(props);
        this.state = {
        };
    }

    async componentDidMount() {
    }

    handleRunJob = async () => {
        console.info('xxxxxxx', repeat_text);
        let result = await window.executeJob(repeat_text, {textfile: 'sha1://7e4bee0355513c30b905507448cac1edd0357e5d/test1.txt', num_repeats: 6})
        if (result.retcode !== 0) {
            console.error('Error running job');
            return;
        }
        console.info(result);
        let txt0 = await this.props.kacheryManager.loadText(result.outputs['textfile_out']);
        console.info(txt0);
    }

    render() {
        return (
            <div>
                <Button onClick={this.handleRunJob}>
                    Run job
                </Button>
            </div>
        );
    }
}

export default class DevTestViewPlugin {
    static getViewComponentsForFile(path, opts) {
        if (baseName(path) === 'geom.csv') {
            return [{
                component: <DevTestView path={path} kacheryManager={opts.kacheryManager} />,
                size: 'large'
            }];
        }
        return [];
    }
    static getViewComponentsForDir(path, dir, opts) {
        return [];
    }
}

function baseName(str) {
    var base = new String(str).substring(str.lastIndexOf('/') + 1);
    return base;
}
