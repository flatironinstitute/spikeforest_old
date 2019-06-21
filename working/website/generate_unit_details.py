#!/usr/bin/env python

import argparse
from mountaintools import client as mt
import os
import json
import multiprocessing
import random

import numpy as np
import spikeextractors as se
from spikeforest import mdaio
from spikeforest_analysis import bandpass_filter
import mlprocessors as mlpr

from spikeforest import SFMdaRecordingExtractor, SFMdaSortingExtractor

# _CONTAINER = 'sha1://5627c39b9bd729fc011cbfce6e8a7c37f8bcbc6b/spikeforest_basic.simg'
# _CONTAINER = 'sha1://0944f052e22de0f186bb6c5cb2814a71f118f2d1/spikeforest_basic.simg' #MAY26JJJ
_CONTAINER = None


def main():
    parser = argparse.ArgumentParser(description='Generate unit detail data (including spikesprays) for website')
    parser.add_argument('--output_ids', help='Comma-separated list of IDs of the analysis outputs to include in the website.', required=False, default=None)

    args = parser.parse_args()

    use_slurm = True

    mt.configDownloadFrom(['spikeforest.kbucket'])

    if args.output_ids is not None:
        output_ids = args.output_ids.split(',')
    else:
        output_ids = [
            'paired_boyden32c',
            'paired_crcns',
            'paired_mea64c',
            'paired_kampff',
            'paired_monotrode',
            'synth_monotrode',
            # 'synth_bionet',
            'synth_magland',
            'manual_franklab',
            'synth_mearec_neuronexus',
            'synth_mearec_tetrode',
            'synth_visapy',
            'hybrid_janelia'
        ]
    print('Using output ids: ', output_ids)

    print('******************************** LOADING ANALYSIS OUTPUT OBJECTS...')
    for output_id in output_ids:
        slurm_working_dir = 'tmp_slurm_job_handler_' + _random_string(5)
        job_handler = mlpr.SlurmJobHandler(
            working_dir=slurm_working_dir
        )
        if use_slurm:
            job_handler.addBatchType(
                name='default',
                num_workers_per_batch=20,
                num_cores_per_job=1,
                time_limit_per_batch=1800,
                use_slurm=True,
                additional_srun_opts=['-p ccm']
            )
        else:
            job_handler.addBatchType(
                name='default',
                num_workers_per_batch=multiprocessing.cpu_count(),
                num_cores_per_job=1,
                use_slurm=False
            )
        with mlpr.JobQueue(job_handler=job_handler) as JQ:
            print('=============================================', output_id)
            print('Loading output object: {}'.format(output_id))
            output_path = ('key://pairio/spikeforest/spikeforest_analysis_results.{}.json').format(output_id)
            obj = mt.loadObject(path=output_path)
            # studies = obj['studies']
            # study_sets = obj.get('study_sets', [])
            # recordings = obj['recordings']
            sorting_results = obj['sorting_results']

            print('Determining sorting results to process ({} total)...'.format(len(sorting_results)))
            sorting_results_to_process = []
            for sr in sorting_results:
                key = dict(
                    name='unit-details-v0.1.0',
                    recording_directory=sr['recording']['directory'],
                    firings_true=sr['firings_true'],
                    firings=sr['firings']
                )
                val = mt.getValue(key=key, collection='spikeforest')
                if not val:
                    sr['key'] = key
                    sorting_results_to_process.append(sr)

            print('Need to process {} of {} sorting results'.format(len(sorting_results_to_process), len(sorting_results)))

            recording_directories_to_process = sorted(list(set([sr['recording']['directory'] for sr in sorting_results_to_process])))
            print('{} recording directories to process'.format(len(recording_directories_to_process)))

            print('Filtering recordings...')
            filter_jobs = FilterTimeseries.createJobs([
                dict(
                    recording_directory=recdir,
                    timeseries_out={'ext': '.mda'},
                    _timeout=600
                )
                for recdir in recording_directories_to_process
            ])
            filter_results = [job.execute() for job in filter_jobs]

            JQ.wait()

            filtered_timeseries_by_recdir = dict()
            for i, recdir in enumerate(recording_directories_to_process):
                result0 = filter_results[i]
                if result0.retcode != 0:
                    raise Exception('Problem computing filtered timeseries for recording: {}'.format(recdir))
                filtered_timeseries_by_recdir[recdir] = result0.outputs['timeseries_out']

            print('Creating spike sprays...')
            for sr in sorting_results_to_process:
                rec = sr['recording']
                study_name = rec['study']
                rec_name = rec['name']
                sorter_name = sr['sorter']['name']

                print('====== COMPUTING {}/{}/{}'.format(study_name, rec_name, sorter_name))

                if sr.get('comparison_with_truth', None) is not None:
                    cwt = mt.loadObject(path=sr['comparison_with_truth']['json'])

                    filtered_timeseries = filtered_timeseries_by_recdir[rec['directory']]

                    spike_spray_job_objects = []
                    list0 = list(cwt.values())
                    for _, unit in enumerate(list0):
                        # print('')
                        # print('=========================== {}/{}/{} unit {} of {}'.format(study_name, rec_name, sorter_name, ii + 1, len(list0)))
                        # ssobj = create_spikesprays(rx=rx, sx_true=sx_true, sx_sorted=sx, neighborhood_size=neighborhood_size, num_spikes=num_spikes, unit_id_true=unit['unit_id'], unit_id_sorted=unit['best_unit'])

                        spike_spray_job_objects.append(dict(
                            args=dict(
                                recording_directory=rec['directory'],
                                filtered_timeseries=filtered_timeseries,
                                firings_true=os.path.join(rec['directory'], 'firings_true.mda'),
                                firings_sorted=sr['firings'],
                                unit_id_true=unit['unit_id'],
                                unit_id_sorted=unit['best_unit'],
                                json_out={'ext': '.json'},
                                _container='default',
                                _timeout=180
                            ),
                            study_name=study_name,
                            rec_name=rec_name,
                            sorter_name=sorter_name,
                            unit=unit
                        ))
                    spike_spray_jobs = CreateSpikeSprays.createJobs([
                        obj['args']
                        for obj in spike_spray_job_objects
                    ])
                    spike_spray_results = [job.execute() for job in spike_spray_jobs]

                    sr['spike_spray_job_objects'] = spike_spray_job_objects
                    sr['spike_spray_results'] = spike_spray_results

            JQ.wait()

        for sr in sorting_results_to_process:
            rec = sr['recording']
            study_name = rec['study']
            rec_name = rec['name']
            sorter_name = sr['sorter']['name']

            print('====== SAVING {}/{}/{}'.format(study_name, rec_name, sorter_name))

            if sr.get('comparison_with_truth', None) is not None:
                spike_spray_job_objects = sr['spike_spray_job_objects']
                spike_spray_results = sr['spike_spray_results']

                unit_details = []
                ok = True
                for i, result in enumerate(spike_spray_results):
                    obj0 = spike_spray_job_objects[i]
                    if result.retcode != 0:
                        print('WARNING: Error creating spike sprays for job:')
                        print(spike_spray_job_objects[i])
                        ok = False
                        break
                    ssobj = mt.loadObject(path=result.outputs['json_out'])
                    if ssobj is None:
                        raise Exception('Problem loading spikespray object output.')
                    address = mt.saveObject(object=ssobj, upload_to='spikeforest.kbucket')
                    unit = obj0['unit']
                    unit_details.append(dict(
                        studyName=obj0['study_name'],
                        recordingName=obj0['rec_name'],
                        sorterName=obj0['sorter_name'],
                        trueUnitId=unit['unit_id'],
                        sortedUnitId=unit['best_unit'],
                        spikeSprayUrl=mt.findFile(path=address, remote_only=True, download_from='spikeforest.kbucket'),
                        _container='default'
                    ))
                if ok:
                    mt.saveObject(collection='spikeforest', key=sr['key'], object=unit_details, upload_to='spikeforest.public')


class FilterTimeseries(mlpr.Processor):
    NAME = 'FilterTimeseries'
    VERSION = '0.1.0'
    CONTAINER = _CONTAINER

    recording_directory = mlpr.Input(description='Recording directory', optional=False, directory=True)
    timeseries_out = mlpr.Output(description='Filtered timeseries file (.mda)')

    def run(self):
        rx = SFMdaRecordingExtractor(dataset_directory=self.recording_directory, download=True)
        rx2 = bandpass_filter(recording=rx, freq_min=300, freq_max=6000, freq_wid=1000)
        if not mdaio.writemda32(rx2.get_traces(), self.timeseries_out):
            raise Exception('Unable to write output file.')


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
    CONTAINER = _CONTAINER

    recording_directory = mlpr.Input(description='Recording directory', optional=False, directory=True)
    filtered_timeseries = mlpr.Input(description='Filtered timeseries file (.mda)', optional=False)
    firings_true = mlpr.Input(description='True firings -- firings_true.mda', optional=False)
    firings_sorted = mlpr.Input(description='Sorted firings -- firings.mda', optional=False)
    unit_id_true = mlpr.IntegerParameter(description='ID of the true unit')
    unit_id_sorted = mlpr.IntegerParameter(description='ID of the sorted unit')
    neighborhood_size = mlpr.IntegerParameter(description='Max size of the electrode neighborhood', optional=True, default=7)
    num_spikes = mlpr.IntegerParameter(description='Max number of spikes in the spike spray', optional=True, default=20)
    json_out = mlpr.Output(description='Output json object')

    def run(self):
        rx = SFMdaRecordingExtractor(dataset_directory=self.recording_directory, download=True, raw_fname=self.filtered_timeseries)
        sx_true = SFMdaSortingExtractor(firings_file=self.firings_true)
        sx = SFMdaSortingExtractor(firings_file=self.firings_sorted)
        ssobj = create_spikesprays(rx=rx, sx_true=sx_true, sx_sorted=sx, neighborhood_size=self.neighborhood_size, num_spikes=self.num_spikes, unit_id_true=self.unit_id_true, unit_id_sorted=self.unit_id_sorted)
        with open(self.json_out, 'w') as f:
            json.dump(ssobj, f)


def _random_string(num_chars):
    chars = 'abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789'
    return ''.join(random.choice(chars) for _ in range(num_chars))


if __name__ == "__main__":
    main()
