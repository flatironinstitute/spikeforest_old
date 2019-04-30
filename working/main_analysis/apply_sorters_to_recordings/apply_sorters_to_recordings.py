import spikeforest_analysis as sa
from mountaintools import client as mt
import numpy as np
import multiprocessing
import mtlogging


@mtlogging.log()
def apply_sorters_to_recordings(*, label, sorters, recordings, studies, study_sets, output_id=None, output_path=None, job_timeout=60*20, upload_to=None):
    # Summarize the recordings
    mtlogging.sublog('summarize-recordings')
    recordings = sa.summarize_recordings(
        recordings=recordings,
        compute_resource='default',
        label='Summarize recordings ({})'.format(label)
    )

    # Run the spike sorting
    mtlogging.sublog('sorting')
    sorting_results = sa.multi_sort_recordings(
        sorters=sorters,
        recordings=recordings,
        label='Sort recordings ({})'.format(label),
        job_timeout=job_timeout,
        upload_to=upload_to
    )

    # Summarize the sortings
    mtlogging.sublog('summarize-sortings')
    sorting_results = sa.summarize_sortings(
        sortings=sorting_results,
        compute_resource='default',
        label='Summarize sortings ({})'.format(label)
    )

    # Compare with ground truth
    mtlogging.sublog('compare-with-truth')
    sorting_results = sa.compare_sortings_with_truth(
        sortings=sorting_results,
        compute_resource='default',
        label='Compare with truth ({})'.format(label),
        upload_to=upload_to
    )

    # Aggregate the results
    mtlogging.sublog('aggregate')
    aggregated_sorting_results = sa.aggregate_sorting_results(
         studies, recordings, sorting_results)

    output_object = dict(
        studies=studies,
        recordings=recordings,
        study_sets=study_sets,
        sorting_results=sorting_results,
        aggregated_sorting_results=mt.saveObject(
            object=aggregated_sorting_results, upload_to=upload_to)
    )

    # Save the output
    if output_id:
        print('Saving the output')
        mtlogging.sublog('save-output')
        mt.saveObject(
            key=dict(
                name='spikeforest_results'
            ),
            subkey=output_id,
            object=output_object,
            upload_to=upload_to
        )
    
    if output_path:
        print('Saving the output to {}'.format(output_path))
        mtlogging.sublog('save-output-path')
        address = mt.saveObject(output_object, upload_to=upload_to)
        if not address:
            raise Exception('Problem saving output object.')
        if not mt.createSnapshot(path=address, dest_path=output_path):
            raise Exception('Problem saving output to {}'.format(output_path))

    mtlogging.sublog('show-output-summary')
    for sr in aggregated_sorting_results['study_sorting_results']:
        study_name = sr['study']
        sorter_name = sr['sorter']
        n1 = np.array(sr['num_matches'])
        n2 = np.array(sr['num_false_positives'])
        n3 = np.array(sr['num_false_negatives'])
        accuracies = n1/(n1+n2+n3)
        avg_accuracy = np.mean(accuracies)
        txt = 'STUDY: {}, SORTER: {}, AVG ACCURACY: {}'.format(
            study_name, sorter_name, avg_accuracy)
        print(txt)
