#!/bin/bash
set -e

# you need pip install j2cli

j2 spike_sorting_spikeforest_recording.md.j2 -o spike_sorting_spikeforest_recording.md
j2 spike_sorting_spikeforest_recording.py.j2 -o spike_sorting_spikeforest_recording.py
chmod a+x spike_sorting_spikeforest_recording.py
