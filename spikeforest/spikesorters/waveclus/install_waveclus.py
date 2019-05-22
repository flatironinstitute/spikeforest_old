import os
from mountaintools import client as mt
import mlprocessors as mlpr
import shutil


def install_waveclus(repo, commit):
    spikeforest_alg_install_path = os.getenv('SPIKEFOREST_ALG_INSTALL_PATH', os.getenv('HOME') + '/spikeforest_algs')
    key = dict(
        alg='waveclus',
        repo=repo,
        commit=commit
    )
    source_path = spikeforest_alg_install_path + '/waveclus_' + commit
    if os.path.exists(source_path):
        # The dir hash method does not seem to be working for some reason here
        # hash0 = mt.computeDirHash(source_path)
        # if hash0 == mt.getValue(key=key):
        #     print('waveclus is already auto-installed.')
        #     return source_path

        a = mt.loadObject(path=source_path + '/spikeforest.json')
        if a:
            if mt.sha1OfObject(a) == mt.sha1OfObject(key):
                print('waveclus is already auto-installed.')
                return source_path

        print('Removing directory: {}'.format(source_path))
        shutil.rmtree(source_path)

    script = """
    #!/bin/bash
    set -e

    git clone {repo} {source_path}
    cd {source_path}
    git checkout {commit}
    """.format(repo=repo, commit=commit, source_path=source_path)
    ss = mlpr.ShellScript(script=script)
    ss.start()
    retcode = ss.wait()
    if retcode != 0:
        raise Exception('Install script returned a non-zero exit code/')

    # The dir hash method does not seem to be working for some reason here
    # hash0 = mt.computeDirHash(source_path)
    # mt.setValue(key=key, value=hash0)
    mt.saveObject(object=key, dest_path=source_path + '/spikeforest.json')

    return source_path
