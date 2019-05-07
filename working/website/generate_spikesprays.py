#!/usr/bin/env python

import argparse
from mountaintools import client as mt
import os
import json

import numpy as np
import spikeextractors as se
from spikeforest_analysis import bandpass_filter
import mlprocessors as mlpr

from spikeforest import SFMdaRecordingExtractor, SFMdaSortingExtractor


def main():
    parser = argparse.ArgumentParser(description='Generate spike spray data for website')
    parser.add_argument('--output_file', help='The output file for saving the spikespray info.', required=False, default=None)
    parser.add_argument('--output_ids', help='Comma-separated list of IDs of the analysis outputs to include in the website.', required=False, default=None)
    parser.add_argument('--upload_to', help='Optional kachery to upload to', required=False, default=None)
    parser.add_argument('--dest_key_path', help='Optional destination key path', required=False, default=None)
    parser.add_argument('--login', help='Whether to log in.', action='store_true')

    args = parser.parse_args()

    if args.login:
        mt.login(ask_password=True)

    output_file = args.output_file

    mt.configDownloadFrom(['spikeforest.kbucket'])

    if args.output_ids is not None:
        output_ids = args.output_ids.split(',')
    else:
        output_ids = [
            'paired_boyden32c',
            'paired_crcns',
            'paired_mea64c',
            'paired_kampff',
            'synth_bionet',
            'synth_magland',
            'manual_franklab',
            'synth_mearec_neuronexus',
            'synth_mearec_tetrode',
            'synth_visapy'
        ]
    print('Using output ids: ', output_ids)

    print('******************************** LOADING ANALYSIS OUTPUT OBJECTS...')
    studies = []
    study_sets = []
    recordings = []
    sorting_results = []
    for output_id in output_ids:
        print('Loading output object: {}'.format(output_id))
        output_path = ('key://pairio/spikeforest/spikeforest_analysis_results.{}.json').format(output_id)
        obj = mt.loadObject(path=output_path)
        studies = studies + obj['studies']
        print(obj.keys())
        study_sets = study_sets + obj.get('study_sets', [])
        recordings = recordings + obj['recordings']
        sorting_results = sorting_results + obj['sorting_results']

    spike_sprays = []
    for sr in sorting_results:
        rec = sr['recording']
        study_name = rec['study']
        rec_name = rec['name']
        sorter_name = sr['sorter']['name']

        # rx = SFMdaRecordingExtractor(dataset_directory=rec['directory'], download=True)
        # sx_true = SFMdaSortingExtractor(firings_file=os.path.join(rec['directory'], 'firings_true.mda'))
        # sx = SFMdaSortingExtractor(firings_file=mt.realizeFile(path=sr['firings']))
        cwt = mt.loadObject(path=sr['comparison_with_truth']['json'])

        list0 = list(cwt.values())
        for ii, unit in enumerate(list0):
            print('')
            print('=========================== {}/{}/{} unit {} of {}'.format(study_name, rec_name, sorter_name, ii + 1, len(list0)))
            # ssobj = create_spikesprays(rx=rx, sx_true=sx_true, sx_sorted=sx, neighborhood_size=neighborhood_size, num_spikes=num_spikes, unit_id_true=unit['unit_id'], unit_id_sorted=unit['best_unit'])
            result = CreateSpikeSprays.execute(
                recording_directory=rec['directory'],
                firings_true=os.path.join(rec['directory'], 'firings_true.mda'),
                firings_sorted=sr['firings'],
                unit_id_true=unit['unit_id'],
                unit_id_sorted=unit['best_unit'],
                json_out={'ext': '.json'}
            )
            if result.retcode != 0:
                raise Exception('Error creating spike sprays')
            ssobj = mt.loadObject(path=result.outputs['json_out'])
            if ssobj is None:
                raise Exception('Problem loading spikespray object output.')
            address = mt.saveObject(object=ssobj, upload_to=args.upload_to)
            spike_sprays.append(dict(
                study=study_name,
                recording=rec_name,
                unit_id_true=unit['unit_id'],
                unit_id_sorted=unit['best_unit'],
                sorter=sorter_name,
                spikespray=address,
                spikespray_http=mt.findFile(path=address, remote_only=True)
            ))
    #
    #         print('Saving to {}'.format(path))
    #         mt.saveObject(dest_path=path, object=ssobj)

    if output_file is not None:
        mt.saveObject(object=spike_sprays, dest_path=output_file)

    address = mt.saveObject(object=spike_sprays)
    mt.createSnapshot(path=address, upload_to=args.upload_to, dest_path=args.dest_key_path)


def _get_random_spike_waveforms(*, recording, sorting, unit, max_num=50, channels=None, snippet_len=100):
    st = sorting.get_unit_spike_train(unit_id=unit)
    num_events = len(st)
    if num_events > max_num:
        event_indices = np.random.choice(
            range(num_events), size=max_num, replace=False)
    else:
        event_indices = range(num_events)

    spikes = recording.get_snippets(reference_frames=st[event_indices].astype(int), snippet_len=snippet_len,
                                    channel_ids=channels)
    if len(spikes) > 0:
        spikes = np.dstack(tuple(spikes))
    else:
        spikes = np.zeros((recording.get_num_channels(), snippet_len, 0))
    return spikes


def get_channels_in_neighborhood(rx, *, central_channel, max_size):
    geom = [rx.get_channel_property(channel_id=ch, property_name='location') for ch in rx.get_channel_ids()]
    loc_central = rx.get_channel_property(channel_id=central_channel, property_name='location')
    dists = [np.sqrt(np.sum((np.array(loc_central) - np.array(loc))**2)) for loc in geom]
    inds = np.argsort(dists)
    if len(inds) > max_size:
        inds = inds[0:max_size]
    chan_ids = rx.get_channel_ids()
    ret = [chan_ids[ind] for ind in inds]
    return ret


def get_unmatched_times(times1, times2, *, delta):
    times1 = np.array(times1)
    times2 = np.array(times2)
    times_concat = np.concatenate((times1, times2))
    membership = np.concatenate(
        (np.ones(times1.shape) * 1, np.ones(times2.shape) * 2))
    indices = times_concat.argsort()
    times_concat_sorted = times_concat[indices]
    membership_sorted = membership[indices]
    diffs = times_concat_sorted[1:] - times_concat_sorted[:-1]
    unmatched_inds = 1 + np.where((diffs[1:] > delta) & (diffs[:-1] > delta) & (membership_sorted[1:-1] == 1))[0]
    if (diffs[0] > delta) and (membership_sorted[0] == 1):
        unmatched_inds = np.concatenate(([0], unmatched_inds))
    if (diffs[-1] > delta) and (membership_sorted[-1] == 1):
        unmatched_inds = np.concatenate(
            (unmatched_inds, [len(membership_sorted) - 1]))
    return times_concat_sorted[unmatched_inds]


def get_unmatched_sorting(sx1, sx2, ids1, ids2):
    ret = se.NumpySortingExtractor()
    for ii in range(len(ids1)):
        id1 = ids1[ii]
        id2 = ids2[ii]
        train1 = sx1.get_unit_spike_train(unit_id=id1)
        train2 = sx2.get_unit_spike_train(unit_id=id2)
        train = get_unmatched_times(train1, train2, delta=100)
        ret.add_unit(id1, train)
    return ret


def create_spikespray_object(waveforms, name, channel_ids):
    return dict(
        name=name,
        num_channels=waveforms.shape[0],
        num_timepoints=waveforms.shape[1],
        num_spikes=waveforms.shape[2],
        channel_ids=channel_ids,
        spike_waveforms=[
            dict(
                channels=[
                    dict(
                        channel_id=ch,
                        waveform=waveforms[ii, :, spike_index].tolist()
                    )
                    for ii, ch in enumerate(channel_ids)
                ]
            )
            for spike_index in range(waveforms.shape[2])
        ]
    )


def create_spikesprays(*, rx, sx_true, sx_sorted, neighborhood_size, num_spikes, unit_id_true, unit_id_sorted):
    rx = bandpass_filter(recording=rx, freq_min=300, freq_max=6000)
    sx_unmatched_true = get_unmatched_sorting(sx_true, sx_sorted, [unit_id_true], [unit_id_sorted])
    sx_unmatched_sorted = get_unmatched_sorting(sx_sorted, sx_true, [unit_id_sorted], [unit_id_true])
    waveforms0 = _get_random_spike_waveforms(recording=rx, sorting=sx_true, unit=unit_id_true)
    avg = np.mean(waveforms0, axis=2)
    peak_chan = np.argmax(np.max(np.abs(avg), axis=1), axis=0)
    nbhd_channels = get_channels_in_neighborhood(rx, central_channel=peak_chan, max_size=7)
    waveforms1 = _get_random_spike_waveforms(recording=rx, sorting=sx_true, unit=unit_id_true, channels=nbhd_channels)
    if unit_id_sorted in sx_sorted.get_unit_ids():
        waveforms2 = _get_random_spike_waveforms(recording=rx, sorting=sx_sorted, unit=unit_id_sorted, channels=nbhd_channels)
    else:
        waveforms2 = np.zeros((waveforms1.shape[0], waveforms1.shape[1], 0))
    if unit_id_true in sx_unmatched_true.get_unit_ids():
        waveforms3 = _get_random_spike_waveforms(recording=rx, sorting=sx_unmatched_true, unit=unit_id_true, channels=nbhd_channels)
    else:
        waveforms3 = np.zeros((waveforms1.shape[0], waveforms1.shape[1], 0))
    if unit_id_sorted in sx_unmatched_sorted.get_unit_ids():
        waveforms4 = _get_random_spike_waveforms(recording=rx, sorting=sx_unmatched_sorted, unit=unit_id_sorted, channels=nbhd_channels)
    else:
        waveforms4 = np.zeros((waveforms1.shape[0], waveforms1.shape[1], 0))

    ret = []
    ret.append(create_spikespray_object(waveforms1, 'true', nbhd_channels))
    ret.append(create_spikespray_object(waveforms2, 'sorted', nbhd_channels))
    ret.append(create_spikespray_object(waveforms3, 'true_missed', nbhd_channels))
    ret.append(create_spikespray_object(waveforms4, 'sorted_false', nbhd_channels))
    return ret


class CreateSpikeSprays(mlpr.Processor):
    NAME = 'CreateSpikeSprays'
    VERSION = '0.1.0'

    recording_directory = mlpr.Input(description='Recording directory', optional=False, directory=True)
    firings_true = mlpr.Input(description='True firings -- firings_true.mda', optional=False)
    firings_sorted = mlpr.Input(description='Sorted firings -- firings.mda', optional=False)
    unit_id_true = mlpr.IntegerParameter(description='ID of the true unit')
    unit_id_sorted = mlpr.IntegerParameter(description='ID of the sorted unit')
    neighborhood_size = mlpr.IntegerParameter(description='Max size of the electrode neighborhood', optional=True, default=7)
    num_spikes = mlpr.IntegerParameter(description='Max number of spikes in the spike spray', optional=True, default=20)
    json_out = mlpr.Output(description='Output json object')

    def run(self):
        rx = SFMdaRecordingExtractor(dataset_directory=self.recording_directory, download=True)
        sx_true = SFMdaSortingExtractor(firings_file=self.firings_true)
        sx = SFMdaSortingExtractor(firings_file=self.firings_sorted)
        ssobj = create_spikesprays(rx=rx, sx_true=sx_true, sx_sorted=sx, neighborhood_size=self.neighborhood_size, num_spikes=self.num_spikes, unit_id_true=self.unit_id_true, unit_id_sorted=self.unit_id_sorted)
        with open(self.json_out, 'w') as f:
            json.dump(ssobj, f)

if __name__ == "__main__":
    main()
