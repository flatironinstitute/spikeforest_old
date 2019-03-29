from mountainlab_pytools import mlproc as mlp
from mountainlab_pytools import mdaio
import spikeextractors as si
from spikeforest import SFMdaRecordingExtractor, SFMdaSortingExtractor
import os
import sys
import numpy as np
import json
from MEArec import SpikeTrainGenerator
from synthesize_timeseries import synthesize_timeseries
import h5py
from scipy import signal
import MEArec as mr
import MEAutility as mu


def gen_synth_datasets(datasets, *, outdir, samplerate=32000):
    if not os.path.exists(outdir):
        os.mkdir(outdir)
    for ds in datasets:
        ds_name = ds['name']
        print(ds_name)
        if 'seed' not in ds.keys():
            ds['seed'] = 0
        spiketrains = gen_spiketrains(
            duration=ds['duration'],
            n_exc=ds['n_exc'],
            n_inh=ds['n_inh'],
            f_exc=ds['f_exc'],
            f_inh=ds['f_inh'],
            min_rate=ds['min_rate'],
            st_exc=ds['st_exc'],
            st_inh=ds['st_inh'],
            seed=ds['seed']
        )
        OX = NeoSpikeTrainsOutputExtractor(
            spiketrains=spiketrains, samplerate=samplerate)
        X, geom = gen_recording(
            templates=ds['templates'],
            output_extractor=OX,
            noise_level=ds['noise_level'],
            samplerate=samplerate,
            duration=ds['duration']
        )
        IX = si.NumpyRecordingExtractor(
            timeseries=X, samplerate=samplerate, geom=geom)
        SFMdaRecordingExtractor.writeRecording(
            IX, outdir+'/{}'.format(ds_name))
        SFMdaSortingExtractor.writeSorting(
            OX, outdir+'/{}/firings_true.mda'.format(ds_name))
    print('Done.')


def gen_spiketrains(*, duration, n_exc, n_inh, f_exc, f_inh, st_exc, st_inh, min_rate, seed=0):
    params_dict = dict(
        duration=duration,
        n_exc=n_exc,
        n_inh=n_inh,
        f_exc=f_exc,
        f_inh=f_inh,
        st_exc=st_exc,
        st_inh=st_inh,
        min_rate=min_rate,
        process='poisson',
        t_start=0,
        ref_per=2,
        seed=seed
    )
    spgen = SpikeTrainGenerator(params_dict)
    spgen.generate_spikes()
    spiketrains = spgen.all_spiketrains
    return spiketrains


def gen_recording(*, templates, output_extractor, noise_level, samplerate, duration):
    OX = output_extractor
    K = len(OX.getUnitIds())
    templates_path = mlp.realizeFile(templates)
    templates_data = {}
    with h5py.File(templates_path, 'r') as F:
        templates_data['info'] = json.loads(str(F['info'][()]))
        templates_data['celltypes'] = np.array(F.get('celltypes'))
        templates_data['locations'] = np.array(F.get('locations'))
        templates_data['rotations'] = np.array(F.get('rotations'))
        templates_data['templates'] = np.array(F.get('templates'))
    templates0 = templates_data['templates']
    template_inds = np.random.choice(
        range(templates0.shape[0]), K, replace=False)
    templates0 = templates0[template_inds, :, :]
    upsample_factor = 13
    templates0_upsampled = signal.resample_poly(
        templates0, up=upsample_factor, down=1, axis=2)
    waveforms0 = templates0_upsampled.transpose([1, 2, 0])

    cut_out = templates_data['info']['params']['cut_out']
    frac = cut_out[0]/(cut_out[0]+cut_out[1])
    waveforms_tcenter = int(frac*waveforms0.shape[1]/upsample_factor)
    X = synthesize_timeseries(output_extractor=OX, waveforms=waveforms0, waveforms_tcenter=waveforms_tcenter,
                              samplerate=samplerate, duration=duration, waveform_upsamplefac=upsample_factor, noise_level=noise_level)

    M = X.shape[0]
    # geom=np.zeros((M,2))
    # geom[:,1]=range(M)
    tempgen_ = mr.load_templates(templates)
    mea_ = mu.return_mea(info=tempgen_.info['electrodes'])
    # make sure the geom matches the dimension of X
    geom = mea_.positions[:M, 1:3]

    # mdaio.writemda32(X,recording_out)
    return X, geom


class NeoSpikeTrainsOutputExtractor(si.SortingExtractor):
    def __init__(self, *, spiketrains, samplerate):
        si.SortingExtractor.__init__(self)
        self._spiketrains = spiketrains
        self._fs = samplerate
        self._num_units = len(spiketrains)
        self._unit_ids = [int(x) for x in range(self._num_units)]

    def getUnitIds(self):
        return self._unit_ids

    def getUnitSpikeTrain(self, unit_id, start_frame=None, end_frame=None):
        if start_frame is None:
            start_frame = 0
        if end_frame is None:
            end_frame = np.Inf
        if self._spiketrains is None:
            self._initialize()
        times = (self._spiketrains[unit_id].times.rescale(
            's') * self._fs).magnitude
        inds = np.where((start_frame <= times) & (times < end_frame))
        return times[inds]

# Wrappers to MEArec processors


def gen_spiketrains_old(spiketrains_out, params):
    mlp.runProcess(
        'mearec.gen_spiketrains',
        inputs=dict(
        ),
        outputs=dict(
            spiketrains_out=spiketrains_out
        ),
        parameters=params,
        opts={}
    )


def gen_recording_old(templates, spiketrains, recording_out, params):
    # ml_mearec.gen_recording()(templates=templates,spiketrains=spiketrains,recording_out=recording_out,**params)
    mlp.runProcess(
        'mearec.gen_recording',
        inputs=dict(
            templates=templates,
            spiketrains=spiketrains
        ),
        outputs=dict(
            recording_out=recording_out
        ),
        parameters=params,
        opts={}
    )
