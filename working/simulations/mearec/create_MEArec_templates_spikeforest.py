import MEArec as mr
from pprint import pprint
from pathlib import Path
from copy import deepcopy

working_folder = Path('spikeforest_data')

template_default_params = mr.get_default_templates_params()
cell_models_folder = mr.get_default_cell_models_folder()
pprint(template_default_params)

print('Generating tetrode templates')
tetrode_params = deepcopy(template_default_params)
tetrode_params['probe'] = 'tetrode-mea-l'
tetrode_params['n'] = 100
tempgen_tetrode = mr.gen_templates(cell_models_folder=cell_models_folder, params=tetrode_params)


print('Generating Neuronexus templates')
neuronexus_params = deepcopy(template_default_params)
neuronexus_params['probe'] = 'Neuronexus-32'
neuronexus_params['n'] = 100
tempgen_neuronexus = mr.gen_templates(cell_models_folder=cell_models_folder, params=neuronexus_params)


print('Generating Neuropixels templates')
neuropixels_params = deepcopy(template_default_params)
neuropixels_params['probe'] = 'Neuropixels-128'
neuropixels_params['n'] = 100
tempgen_neuropixels = mr.gen_templates(cell_models_folder=cell_models_folder, params=neuropixels_params)


print('Generating Neuronexus drifting templates')
neuronexus_params_drift = deepcopy(template_default_params)
neuronexus_params_drift['probe'] = 'Neuronexus-32'
neuronexus_params_drift['n'] = 100
neuronexus_params_drift['drifting'] = True
tempgen_neuronexus_drift = mr.gen_templates(cell_models_folder=cell_models_folder, params=neuronexus_params_drift)


print('Saving templates')
mr.save_template_generator(tempgen_tetrode, working_folder / 'templates' / 'templates_tetrode.h5')
mr.save_template_generator(tempgen_neuronexus, working_folder / 'templates' / 'templates_neuronexus.h5')
mr.save_template_generator(tempgen_neuropixels, working_folder / 'templates' / 'templates_neuropixels.h5')
mr.save_template_generator(tempgen_neuronexus_drift, working_folder / 'templates' / 'templates_neuronexus_drift.h5')
