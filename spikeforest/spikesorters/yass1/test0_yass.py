# %% Change working directory from the workspace root to the ipynb file location. Turn this addition off with the DataScience.changeDirOnImportExport setting
from mountaintools import client as mt
import sfdata as sf
import spikeforest_analysis as sa
import os
try:
    os.chdir(os.path.join(os.getcwd(), 'working/spikeforest_test1'))
    print(os.getcwd())
except:
    pass

# %%
# path=ca.saveFile('/mnt/home/jjun/src/sf2dev/spikesorters/containers/yass/yass.simg')
# print(path)

# %%
get_ipython().run_line_magic('load_ext', 'autoreload')
get_ipython().run_line_magic('autoreload', '2')


# %%
password = os.environ.get('SPIKEFOREST_PASSWORD', None)
mt.autoConfig(collection='spikeforest', key='spikeforest2-readwrite',
              password=password, ask_password=True)


# %%
os.environ['MLPROCESSORS_FORCE_RUN'] = 'TRUE'
recording = dict(
    directory='kbucket://15734439d8cf/groundtruth/magland_synth/datasets_noise10_K10_C4/001_synth')
recordings = [recording]


# %%
sorter_ms4_thr3 = dict(
    name='MountainSort4-thr3',
    processor_name='MountainSort4',
    params=dict(
        detect_sign=-1,
        adjacency_radius=50,
        detect_threshold=3.1
    )
)

sorter_sc = dict(
    name='SpykingCircus',
    processor_name='SpykingCircus',
    params=dict(
        detect_sign=-1,
        adjacency_radius=50
    )
)

sorter_yass = dict(
    name='yass',
    processor_name='yass',
    params=dict(
        detect_sign=-1,
        adjacency_radius=50
    )
)
# sorters=[sorter_ms4_thr3,sorter_sc,sorter_yass]
# sorters=[sorter_yass]
sorters = [sorter_sc]


# %%
# compute_resource='jfm-laptop'
compute_resource = None
recordings_B = sa.summarize_recordings(
    recordings=recordings, compute_resource=compute_resource)
sorting_results = []
for sorter in sorters:
    sortings_A = sa.sort_recordings(
        sorter=sorter, recordings=recordings_B, compute_resource=compute_resource)
    sortings_B = sa.summarize_sortings(
        sortings=sortings_A, compute_resource=compute_resource)
    sortings_C = sa.compare_sortings_with_truth(
        sortings=sortings_B, compute_resource=compute_resource)
    sorting_results = sorting_results+sortings_C


# %%
sortings_A


# %%
summaries = sa.summarize_recordings(
    recordings=[recording], compute_resource=None)  # 'ccmlin008-default')
recording['summary'] = summaries[0]


# %%
sorter_ms4_thr3 = dict(
    name='MountainSort4-thr3',
    processor_name='MountainSort4',
    params=dict(
        detect_sign=-1,
        adjacency_radius=50,
        detect_threshold=3.1
    )
)

sorter_sc = dict(
    name='SpykingCircus',
    processor_name='SpykingCircus',
    params=dict(
        detect_sign=-1,
        adjacency_radius=50
    )
)

sorter_yass = dict(
    name='yass',
    processor_name='yass',
    params=dict(
        detect_sign=-1,
        adjacency_radius=50
    )

)

compute_resource = None
sorting_ms4 = sa.sort_recordings(
    recordings=[recording], sorter=sorter_ms4_thr3, compute_resource=compute_resource)[0]
sorting_sc = sa.sort_recordings(
    recordings=[recording], sorter=sorter_sc, compute_resource=compute_resource)[0]
# sorting_yass=sa.sort_recordings(recordings=[recording],sorter=sorter_yass,compute_resource=compute_resource)[0]


# %%
display(sorting_ms4)
print(mt.loadText(path=sorting_ms4['console_out'])[0:1000])
display(sorting_sc)
print(mt.loadText(path=sorting_sc['console_out'])[0:1000])


# %%
sorting_ms4['summary'] = sa.summarize_sortings(
    sortings=[sorting_ms4], compute_resource=compute_resource)
sorting_ms4['comparison_with_truth'] = sa.compare_sortings_with_truth(
    sortings=[sorting_ms4], compute_resource=compute_resource)


# %%
sorting_ms4


# %%
mt.loadObject(
    path='sha1://cbc3f0d7beb8f94d3bf4287b38ca4b05782f94ec/table.json')


# %%
