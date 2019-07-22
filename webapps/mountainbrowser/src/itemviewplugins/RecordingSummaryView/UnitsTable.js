import React, { Component } from 'react';
import { Table, TableHead, TableRow, TableCell, TableBody } from '@material-ui/core';

function HeaderRow(props) {
    return (
        <TableRow>
            {
                props.columns.map((cc) => (
                    <TableCell key={cc.name}>{cc.label}</TableCell>
                ))
            }
        </TableRow>
    );
}

function UnitRow(props) {
    const { unitInfo } = props;
    return (
        <TableRow hover selected={props.selected} onClick={props.onClick}>
            {
                props.columns.map((cc) => {
                    let val = unitInfo[cc.name];
                    val = (val !== undefined) ? val : '';
                    return <TableCell key={cc.name}>{val}</TableCell>
                })
            }
        </TableRow>
    );
}

export default class UnitsTable extends Component {
    state = {
        selectedUnitId: null
    }
    columns = [
        {
            name: 'unit_id',
            label: 'Unit ID'
        },
        {
            name: 'num_events',
            label: 'Num. events'
        },
        {
            name: 'snr',
            label: 'SNR'
        },
        {
            name: 'peak_channel',
            label: 'Peak chan.'
        },
        {
            name: 'firing_rate',
            label: 'Firing rate (Hz)'
        }
    ]
    selectUnit = (unitInfo) => {
        this.setState({
            selectedUnitId: unitInfo.unit_id
        });
        this.props.onUnitSelected && this.props.onUnitSelected(unitInfo);
    }
    render() {
        const { unitsInfo } = this.props;
        return (
            <Table>
                <TableHead>
                    <HeaderRow columns={this.columns} />
                </TableHead>
                <TableBody>
                    {unitsInfo.map((ui) => (
                        <UnitRow
                            onClick={() => {this.selectUnit(ui)}}
                            columns={this.columns}
                            unitInfo={ui} key={ui.unit_id}
                            selected={ui.unit_id === this.state.selectedUnitId}
                        />
                    ))};
                </TableBody>
            </Table>
        );
    }
}