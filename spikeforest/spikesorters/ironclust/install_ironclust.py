import os
from mountaintools import client as mt
import mlprocessors as mlpr
import shutil
import json
from mountainclient import FileLock


def install_ironclust(commit):
    spikeforest_alg_install_path = os.getenv('SPIKEFOREST_ALG_INSTALL_PATH', os.getenv('HOME') + '/spikeforest_algs')
    repo = 'https://github.com/jamesjun/ironclust'
    key = dict(
        alg='ironclust',
        repo=repo,
        commit=commit
    )
    source_path = spikeforest_alg_install_path + '/ironclust_' + commit
    with FileLock(source_path + '.lock', exclusive=True):
        if not os.path.exists(source_path + '/spikeforest.json'):
            if os.path.exists(source_path):
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

            with open(source_path + '/spikeforest.json', 'w') as f:
                json.dump(key, f)

    return source_path
