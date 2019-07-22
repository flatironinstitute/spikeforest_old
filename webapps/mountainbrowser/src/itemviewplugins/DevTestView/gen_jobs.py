#!/usr/bin/env python

import mlprocessors as mlpr
from mountaintools import client as mt
import spikeforest_analysis as sa


class RepeatText(mlpr.Processor):
    textfile = mlpr.Input(help="input text file")
    textfile_out = mlpr.Output(help="output text file")
    num_repeats = mlpr.IntegerListParameter(
        help="Number of times to repeat the text")

    def run(self):
        assert self.num_repeats >= 0
        with open(self.textfile, 'r') as f:
            txt = f.read()
        txt2 = ''
        for _ in range(self.num_repeats):
            txt2 = txt2 + txt
        with open(self.textfile_out, 'w') as f:
            f.write(txt2)


def main():
    job = RepeatText.createJob(textfile=mlpr.PLACEHOLDER, textfile_out=dict(
        ext='.txt'), num_repeats=mlpr.PLACEHOLDER)
    mt.saveObject(object=job.getObject(),
                  dest_path='repeat_text.json', indent=4)

    job = sa.ComputeRecordingInfo.createJob(
        recording_dir=mlpr.PLACEHOLDER,
        channels=[],
        json_out={'ext': '.json'},
        _container='default'
    )
    mt.saveObject(
        object=job.getObject(),
        dest_path='ComputeRecordingInfo.json',
        indent=4
    )


if __name__ == '__main__':
    main()
