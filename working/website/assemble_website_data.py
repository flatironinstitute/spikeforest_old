#!/usr/bin/env python

import argparse
from mountaintools import client as mt
import os
import frontmatter

help_txt = """
This script saves collections in the following .json files in an output directory

StudySets.json
Studies.json
Recordings.json
TrueUnits.json
UnitResults.json
Sorters.json

## Schema

StudySet
* name (str)
* [type (str) -- synthetic, real, hybrid, etc.]
* [description (str)]
    
Study
* name (str)
* studySet (str)
* description (str)
* sorterNames (array of str)

Note: study name is unique, even across study sets
    
Recording
* name (str)
* study (str)
* directory (str) -- i.e., kbucket address
* description (str)
* sampleRateHz (float)
* numChannels (int)
* durationSec (float)
* numTrueUnits (int)
* [fileSizeBytes (int)]
* spikeSign (int) [Hard-coded for now. In future, grab from params.json]

TrueUnit
* unitId (int)
* recording (str)
* study (str)
* meanFiringRateHz (float)
* numEvents (int)
* peakChannel (int)
* snr (float)

SortingResult
* recording (str)
* recordingExt (str)
* study (str)
* sorter (str)
* cpuTimeSec (float)
* [runtime_info (object): timestamps, wall time, CPU time, RAM usage, error status]
* [firingsOutputUrl (str)] TODO: jfm (two weeks)

UnitResult
* unitId (int)
* recording (str)
* recordingExt (str)
* study (str)
* sorter (str)
* numMatches (int)
* numFalsePositives (int)
* numFalseNegatives (int)
* checkAccuracy (float)
* checkRecall (float)
* checkPrecision (float)
* bestSortedUnitId (int)
* spikeSprayUrl (str) TODO: jfm to make this (next week)

Sorter
* name (str)
* algorithm (str)
* [algorithmVersion (str)] - future
* processorName (str)
* processorVersion (str)
* sortingParameters (object)

Algorithm
* label
* processor_name
"""


def main():
    parser = argparse.ArgumentParser(description=help_txt, formatter_class=argparse.RawTextHelpFormatter)
    parser.add_argument('--output_dir', help='The output directory for saving the files.', required=False, default=None)
    parser.add_argument('--output_ids', help='Comma-separated list of IDs of the analysis outputs to include in the website.', required=False, default=None)
    parser.add_argument('--upload_to', help='Optional kachery to upload to', required=False, default=None)
    parser.add_argument('--dest_key_path', help='Optional destination key path', required=False, default=None)
    parser.add_argument('--login', help='Whether to log in.', action='store_true')

    args = parser.parse_args()

    if args.login:
        mt.login(ask_password=True)

    output_dir = args.output_dir

    if output_dir is not None:
        if os.path.exists(output_dir):
            raise Exception('Output directory already exists: {}'.format(output_dir))

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

    if output_dir is not None:
        os.mkdir(output_dir)

    # ALGORITHMS
    print('******************************** ASSEMBLING ALGORITHMS...')
    algorithms_by_processor_name = dict()
    Algorithms = []
    basepath = '../../spikeforest/spikesorters/descriptions'
    repo_base_url = 'https://github.com/flatironinstitute/spikeforest/blob/master'
    for item in os.listdir(basepath):
        if item.endswith('.md'):
            alg = frontmatter.load(basepath + '/' + item).to_dict()
            alg['markdown_link'] = repo_base_url + '/spikeforest/spikesorters/descriptions/' + item
            alg['markdown'] = alg['content']
            del alg['content']
            if 'processor_name' in alg:
                algorithms_by_processor_name[alg['processor_name']] = alg
            Algorithms.append(alg)
    print([alg['label'] for alg in Algorithms])
    if output_dir is not None:
        mt.saveObject(object=Algorithms, dest_path=os.path.abspath(os.path.join(output_dir, 'Algorithms.json')))

    # STUDY SETS
    print('******************************** ASSEMBLING STUDY SETS...')
    StudySets = []
    for study_set in study_sets:
        StudySets.append(study_set)
    if output_dir is not None:
        mt.saveObject(object=StudySets, dest_path=os.path.abspath(os.path.join(output_dir, 'StudySets.json')))
    print(StudySets)

    # RECORDINGS and TRUE UNITS
    print('******************************** ASSEMBLING RECORDINGS and TRUE UNITS...')
    Recordings = []
    TrueUnits = []
    for recording in recordings:
        true_units_info = mt.loadObject(path=recording['summary']['true_units_info'])
        for unit_info in true_units_info:
            TrueUnits.append(dict(
                unitId=unit_info['unit_id'],
                recording=recording['name'],
                recordingExt=recording['study'] + ':' + recording['name'],
                study=recording['study'],
                meanFiringRateHz=unit_info['firing_rate'],
                numEvents=unit_info['num_events'],
                peakChannel=unit_info['peak_channel'],
                snr=unit_info['snr'],
            ))
        Recordings.append(dict(
            name=recording['name'],
            study=recording['study'],
            directory=recording['directory'],
            description=recording['description'],
            sampleRateHz=recording['summary']['computed_info']['samplerate'],
            numChannels=recording['summary']['computed_info']['num_channels'],
            durationSec=recording['summary']['computed_info']['duration_sec'],
            numTrueUnits=len(true_units_info),
            spikeSign=-1
        ))
    if output_dir is not None:
        mt.saveObject(object=Recordings, dest_path=os.path.abspath(os.path.join(output_dir, 'Recordings.json')))
        mt.saveObject(object=TrueUnits, dest_path=os.path.abspath(os.path.join(output_dir, 'TrueUnits.json')))
    print('Num recordings:', len(Recordings))
    print('Num true units:', len(TrueUnits))
    print('studies for recordings:', set([recording['study'] for recording in Recordings]))

    # UNIT RESULTS and SORTING RESULTS
    print('******************************** ASSEMBLING UNIT RESULTS and SORTING RESULTS...')
    UnitResults = []
    SortingResults = []
    sorter_names_by_study = dict()
    for sr in sorting_results:
        if sr.get('comparison_with_truth', None):
            SortingResults.append(dict(
                recording=sr['recording']['name'],
                study=sr['recording']['study'],
                sorter=sr['sorter']['name'],
                cpuTimeSec=sr['execution_stats'].get('elapsed_sec', None)
            ))
            comparison_with_truth = mt.loadObject(path=sr['comparison_with_truth']['json'])
            if comparison_with_truth is None:
                print(sr)
                raise Exception('Unable to retrieve comparison with truth object for sorting result.')
            for unit_result in comparison_with_truth.values():
                study_name = sr['recording']['study']
                sorter_name = sr['sorter']['name']
                if study_name not in sorter_names_by_study:
                    sorter_names_by_study[study_name] = set()
                sorter_names_by_study[study_name].add(sorter_name)
                n_match = unit_result['num_matches']
                n_fp = unit_result['num_false_positives']
                n_fn = unit_result['num_false_negatives']
                if n_match + n_fp > 0:
                    precision = n_match / (n_match + n_fp)
                else:
                    precision = 0
                UnitResults.append(dict(
                    unitId=unit_result['unit_id'],
                    recording=sr['recording']['name'],
                    recordingExt=sr['recording']['study'] + ':' + sr['recording']['name'],
                    study=study_name,
                    sorter=sorter_name,
                    numMatches=n_match,
                    numFalsePositives=n_fp,
                    numFalseNegatives=n_fn,
                    checkAccuracy=n_match / (n_match + n_fp + n_fn),
                    checkPrecision=precision,
                    checkRecall=n_match / (n_match + n_fn),
                    bestSortedUnitId=unit_result['best_unit']
                ))
        else:
            print('Warning: comparison with truth not found for sorting result: {} {}/{}'.format(sr['sorter']['name'], sr['recording']['study'], sr['recording']['name']))
            print('Console output is here: ' + sr['console_out'])
    for study in sorter_names_by_study.keys():
        sorter_names_by_study[study] = list(sorter_names_by_study[study])
        sorter_names_by_study[study].sort()
    if output_dir is not None:
        mt.saveObject(object=UnitResults, dest_path=os.path.abspath(os.path.join(output_dir, 'UnitResults.json')))
        mt.saveObject(object=SortingResults, dest_path=os.path.abspath(os.path.join(output_dir, 'SortingResults.json')))
    print('Num unit results:', len(UnitResults))

    # SORTERS
    print('******************************** ASSEMBLING SORTERS...')
    sorters_by_name = dict()
    for sr in sorting_results:
        sorters_by_name[sr['sorter']['name']] = sr['sorter']
    Sorters = []
    for _, sorter in sorters_by_name.items():
        alg = algorithms_by_processor_name.get(sorter['processor_name'], dict())
        alg_label = alg.get('label', sorter['processor_name'])
        Sorters.append(dict(
            name=sorter['name'],
            algorithm=alg_label,
            processorName=sorter['processor_name'],
            processorVersion='0',  # jfm needs to provide this
            sorting_parameters=sorter['params']  # Liz, even though most sorters have similar parameter names, it won't always be like that. The params is an arbitrary json object.
        ))
    if output_dir is not None:
        mt.saveObject(object=Sorters, dest_path=os.path.abspath(os.path.join(output_dir, 'Sorters.json')))
    print([S['name'] + ':' + S['algorithm'] for S in Sorters])

    # STUDY ANALYSIS RESULTS
    print('******************************** ASSEMBLING STUDY ANALYSIS RESULTS...')
    sorter_names = sorted(list(set([sr['sorter']['name'] for sr in sorting_results])))
    StudyAnalysisResults = [
        _assemble_study_analysis_result(
            study_name=study['name'],
            recordings=recordings,
            sorting_results=sorting_results,
            sorter_names=sorter_names
        )
        for study in studies
    ]
    if output_dir is not None:
        mt.saveObject(object=StudyAnalysisResults, dest_path=os.path.abspath(os.path.join(output_dir, 'StudyAnalysisResults.json')))

    # STUDIES
    print('******************************** ASSEMBLING STUDIES...')
    Studies = []
    for study in studies:
        Studies.append(dict(
            name=study['name'],
            studySet=study['study_set'],
            description=study['description'],
            sorterNames=sorter_names_by_study[study['name']]
            # the following can be obtained from the other collections
            # numRecordings, sorters, etc...
        ))
    if output_dir is not None:
        mt.saveObject(object=Studies, dest_path=os.path.abspath(os.path.join(output_dir, 'Studies.json')))
    print([S['name'] for S in Studies])

    obj = dict(
        mode='spike-front',
        StudySets=StudySets,
        Recordings=Recordings,
        TrueUnits=TrueUnits,
        UnitResults=UnitResults,
        SortingResults=SortingResults,
        Sorters=Sorters,
        Studies=Studies,
        Algorithms=Algorithms,
        StudyAnalysisResults=StudyAnalysisResults
    )
    address = mt.saveObject(object=obj)
    mt.createSnapshot(path=address, upload_to=args.upload_to, dest_path=args.dest_key_path)


def _assemble_study_analysis_result(*, study_name, recordings, sorting_results, sorter_names):
    true_units = dict()
    recording_names = []
    irec = 0
    for rec in recordings:
        if rec['study'] == study_name:
            recording_names.append(rec['name'])
            true_units_info = mt.loadObject(path=rec['summary']['true_units_info'])
            for unit_info in true_units_info:
                id0 = unit_info['unit_id']
                true_units[study_name + '/' + rec['name'] + '/{}'.format(id0)] = dict(
                    unit_id=id0,
                    recording_index=irec,
                    snr=unit_info['snr'],
                    firing_rate=unit_info['firing_rate'],
                    num_events=unit_info['num_events'],
                    sorting_results=dict()
                )
            irec = irec + 1
    cpu_times_by_sorter = dict()
    for sorter_name in sorter_names:
        cpu_times_by_sorter[sorter_name] = []
    for sr in sorting_results:
        rec = sr['recording']
        if rec['study'] == study_name:
            if sr.get('comparison_with_truth', None):
                comparison_with_truth = mt.loadObject(path=sr['comparison_with_truth']['json'])
                if comparison_with_truth is None:
                    print(sr)
                    raise Exception('Unable to retrieve comparison with truth object for sorting result.')
                sorter_name = sr['sorter']['name']
                for unit_result in comparison_with_truth.values():
                    id0 = unit_result['unit_id']
                    n_match = unit_result['num_matches']
                    n_fp = unit_result['num_false_positives']
                    n_fn = unit_result['num_false_negatives']
                    accuracy = n_match / (n_match + n_fp + n_fn)
                    if n_match + n_fp > 0:
                        precision = n_match / (n_match + n_fp)
                    else:
                        precision = 0
                    recall = n_match / (n_match + n_fn)
                    true_units[study_name + '/' + rec['name'] + '/{}'.format(id0)]['sorting_results'][sorter_name] = dict(
                        accuracy=accuracy,
                        precision=precision,
                        recall=recall,
                    )
                cpu_times_by_sorter[sorter_name].append(sr['execution_stats'].get('elapsed_sec', None))
            else:
                cpu_times_by_sorter[sorter_name].append(None)

    keys0 = sorted(true_units.keys())
    true_units_list = [true_units[key] for key in keys0]

    snrs = [_round(x['snr'], 3) for x in true_units_list]
    firing_rates = [_round(x['firing_rate'], 3) for x in true_units_list]
    num_events = [x['num_events'] for x in true_units_list]
    recording_indices = [x['recording_index'] for x in true_units_list]
    unit_ids = [x['unit_id'] for x in true_units_list]

    study_analysis_result = dict(
        studyName=study_name,
        recordingNames=recording_names,
        trueSnrs=snrs,
        trueFiringRates=firing_rates,
        trueNumEvents=num_events,
        trueRecordingIndices=recording_indices,
        trueUnitIds=unit_ids,
        sortingResults=[]
    )
    for sorter_name in sorter_names:
        accuracies = [_round(x['sorting_results'].get(sorter_name, {}).get('accuracy'), 3) for x in true_units_list]
        precisions = [_round(x['sorting_results'].get(sorter_name, {}).get('precision'), 3) for x in true_units_list]
        recalls = [_round(x['sorting_results'].get(sorter_name, {}).get('recall'), 3) for x in true_units_list]
        study_analysis_result['sortingResults'].append(dict(
            sorterName=sorter_name,
            accuracies=accuracies,
            precisions=precisions,
            recalls=recalls,
            cpuTimesSec=cpu_times_by_sorter[sorter_name]
        ))
    print(study_analysis_result['studyName'], study_analysis_result['sortingResults'][0]['cpuTimesSec'])

    return study_analysis_result


def _round(x, num):
    if x is None:
        return None
    return round(x, num)

if __name__ == "__main__":
    main()
