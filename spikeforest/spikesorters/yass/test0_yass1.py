# %% Change working directory from the workspace root to the ipynb file location. Turn this addition off with the DataScience.changeDirOnImportExport setting
import os
try:
    os.chdir(os.path.join(os.getcwd(), 'working/spikeforest_test1'))
    print(os.getcwd())
except:
    pass

# %%
import spikeforest_analysis as sa
from spikeforest_analysis.compare_sortings_with_truth import GenSortingComparisonTable
#from cairio import client as ca
import spikeforest.spikeextractors as se
import os
from spikesorters import YASS
from spikeforest.spiketoolkit.comparison.sortingcomparison import SortingComparison
import spikeforest.spikewidgets as sw

# %%SortingComparisonyass_test1/recording/raw.mda
tmpdir = 'yass_test1'
if not os.path.isdir(tmpdir):
    os.mkdir(tmpdir)
rx, sx = se.example_datasets.yass_example(set_id=1)

# %%
firings_true = tmpdir+'/recording/firings_true.mda'
recording_path = tmpdir+'/recording'
se.MdaRecordingExtractor.writeRecording(
    recording=rx, save_path=recording_path)
se.MdaSortingExtractor.writeSorting(
    sorting=sx, save_path=firings_true)

YASS.execute(
    recording_dir=tmpdir+'/recording',
    firings_out=tmpdir+'/firings_out.mda',
    detect_sign=-1,
    adjacency_radius=50,
    _container=None,
    _force_run=True,
    _keep_temp_files=True
)
firings_out = tmpdir+'/firings_out.mda'
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
    json_out=os.path.join(tmpdir, 'out.json'),
    html_out=os.path.join(tmpdir, 'out.html'),
    _container=None
)


# %%
