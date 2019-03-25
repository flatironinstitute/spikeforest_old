import spikeforest_analysis as sa
from mountaintools import client as mt
import numpy as np
import multiprocessing
import mtlogging


@mtlogging.log()
def apply_sorters_to_recordings(*, sorters, recordings, studies, output_id):
    # Summarize the recordings
    recordings = sa.summarize_recordings(
        recordings=recordings,
        compute_resource='default',
        label='Summarize recordings ({})'.format(output_id)
    )

    # We will be assembling the sorting results here
    sorting_results = []
    for sorter in sorters:
        sorting_results = sorting_results + _run_sorter(sorter=sorter, recordings=recordings, label='{} ({})'.format(sorter['name'], output_id))

    # Summarize the sortings
    sorting_results = sa.summarize_sortings(
        sortings=sorting_results,
        compute_resource='default',
        label='Summarize sortings ({})'.format(output_id)
    )

    # Compare with ground truth
    sorting_results = sa.compare_sortings_with_truth(
        sortings=sorting_results,
        compute_resource='default',
        label='Compare with truth ({})'.format(output_id)
    )

    # Aggregate the results
    aggregated_sorting_results = sa.aggregate_sorting_results(
         studies, recordings, sorting_results)

    # Save the output
    print('Saving the output')
    mt.saveObject(
        key=dict(
            name='spikeforest_results'
        ),
        subkey=output_id,
        object=dict(
            studies=studies,
            recordings=recordings,
            sorting_results=sorting_results,
            aggregated_sorting_results=mt.saveObject(
                object=aggregated_sorting_results)
        )
    )

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

@mtlogging.log()
def _run_sorter(sorter, recordings, label):
    # Sort the recordings
    compute_resource0 = sorter['compute_resource']
    sortings = sa.sort_recordings(
        sorter=sorter,
        recordings=recordings,
        compute_resource=compute_resource0,
        label=label
    )

    return sortings
