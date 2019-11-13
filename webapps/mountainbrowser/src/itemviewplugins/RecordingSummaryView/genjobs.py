#!/usr/bin/env python

import mlprocessors as mlpr
from mountaintools import client as mt
import spikeforest_analysis as sa
from computeunitdetail import ComputeUnitDetail, FilterTimeseries

def genjob(*, processor: mlpr.Processor, fname: str, processor_args: dict) -> None:
    job = processor.createJob(
        **processor_args
    )
    mt.saveObject(object=job.getObject(), dest_path=fname)

def main():
    genjob(
        processor=sa.ComputeRecordingInfo,
        fname='ComputeRecordingInfo.json',
        processor_args=dict(
            recording_dir=mlpr.PLACEHOLDER,
            channels=[],
            json_out={'ext': '.json'},
            _container='default'
        )
    )

    genjob(
        processor=sa.ComputeUnitsInfo,
        fname='ComputeUnitsInfo.json',
        processor_args=dict(
            recording_dir=mlpr.PLACEHOLDER,
            firings=mlpr.PLACEHOLDER,
            unit_ids=None,
            channel_ids=None,
            json_out={'ext': '.json'},
            _container='default',
        )
    )

    genjob(
        processor=FilterTimeseries,
        fname='FilterTimeseries.json',
        processor_args=dict(
            recording_directory=mlpr.PLACEHOLDER,
            timeseries_out={'ext': '.mda'},
            _container='default'
        )
    )

    genjob(
        processor=ComputeUnitDetail,
        fname='ComputeUnitDetail.json',
        processor_args=dict(
            recording_dir=mlpr.PLACEHOLDER,
            firings=mlpr.PLACEHOLDER,
            unit_id=mlpr.PLACEHOLDER,
            json_out={'ext': '.json'},
            _container='default',
        )
    )


if __name__ == '__main__':
    main()
