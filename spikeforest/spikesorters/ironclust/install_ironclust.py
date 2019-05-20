import os
from mountaintools import client as mt
import mlprocessors as mlpr
import shutil


def install_ironclust(commit):
    spikeforest_alg_install_path = os.getenv('SPIKEFOREST_ALG_INSTALL_PATH', os.getenv('HOME') + '/spikeforest_algs')
    repo = 'https://github.com/jamesjun/ironclust'
    key = dict(
        alg='ironclust',
        repo=repo,
        commit=commit
    )
    source_path = spikeforest_alg_install_path + '/ironclust_' + commit
    if os.path.exists(source_path):
        hash0 = mt.computeDirHash(source_path)
        if hash0 == mt.getValue(key=key):
            print('IronClust is already auto-installed.')
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

    hash0 = mt.computeDirHash(source_path)
    mt.setValue(key=key, value=hash0)

    return source_path
