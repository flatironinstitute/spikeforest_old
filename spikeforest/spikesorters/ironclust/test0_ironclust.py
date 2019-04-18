
# %% Change working directory from the workspace root to the ipynb file location. Turn this addition off with the DataScience.changeDirOnImportExport setting
import os
try:
    os.chdir(os.path.join(os.getcwd(), 'ironclust_test'))
    print(os.getcwd())
except:
    pass

# %% python magic
#get_ipython().run_line_magic('load_ext', 'autoreload')
#get_ipython().run_line_magic('autoreload', '2')

# %%
import spikeforest_analysis as sa
from spikeforest_analysis.compare_sortings_with_truth import GenSortingComparisonTable
#from mountaintools import client as ca
import spikeextractors as se
from spikeforest import SFMdaRecordingExtractor, SFMdaSortingExtractor, example_datasets
import os
from spikeforest_analysis.sorters import ironclust
from spikeforest import SortingComparison
from spikeforest import spikewidgets as sw
from spikesorters import IronClust

# %%SortingComparisonyass_test1/recording/raw.mda
""" recording_path = 'irc_test1'
if not os.path.isdir(recording_path):
    os.mkdir(recording_path)
rx, sx = example_datasets.yass_example(set_id=1) """

# %%
recording_path = 'kbucket://15734439d8cf/groundtruth/visapy_mea/set1'
firings_true = recording_path+'/firings_true.mda'
#recording_path = recording_path+'/recording'
# SFMdaRecordingExtractor.writeRecording(
# recording=rx, save_path=recording_path)
# SFMdaSortingExtractor.writeSorting(
# sorting=sx, save_path=firings_true)
result_path = os.path.abspath('test_irc')
if not os.path.exists(result_path):
    os.mkdir(result_path)
firings_out = os.path.join(result_path, 'firings_out.mda')
print('output stored in: ', firings_out)

IronClust.execute(
    recording_dir=recording_path,
    firings_out=firings_out,
    prm_template_name='static',
    detect_sign=-1,
    adjacency_radius=50,
    _container=None,
    _force_run=True,
    _keep_temp_files=True
)
#firings_out = recording_path+'/firings_out.mda'
assert os.path.exists(firings_out)


# %%
print('recording: {}'.format(recording_path))
print('firings_out: {}'.format(firings_out))
print('firings_true: {}'.format(firings_true))

# %%
GenSortingComparisonTable.execute(
    firings=firings_out,
    firings_true=firings_true,
    units_true=[],
    json_out=os.path.join(recording_path, 'out.json'),
    html_out=os.path.join(recording_path, 'out.html'),
    _container=None
)


# %%


# %%
