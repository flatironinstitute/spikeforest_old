import os
from mountaintools import client as mt
import mlprocessors as mlpr
import shutil


def install_jrclust(repo, commit):
    spikeforest_alg_install_path = os.getenv('SPIKEFOREST_ALG_INSTALL_PATH', os.getenv('HOME') + '/spikeforest_algs')
    key = dict(
        alg='jrclust',
        repo=repo,
        commit=commit
    )
    source_path = spikeforest_alg_install_path + '/jrclust_' + commit
    if os.path.exists(source_path):
        # The dir hash method does not seem to be working for some reason here
        # hash0 = mt.computeDirHash(source_path)
        # if hash0 == mt.getValue(key=key):
        #     print('jrclust is already auto-installed.')
        #     return source_path

        a = mt.loadObject(path=source_path + '/spikeforest.json')
        if a:
            if mt.sha1OfObject(a) == mt.sha1OfObject(key):
                print('jrclust is already auto-installed.')
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

    compile_gpu = mlpr.ShellScript(script="""
    function compile_gpu

    try
        jrc compile
    catch
        disp('Problem running `jrc compile`');
        disp(lasterr());
        exit(-1)
    end;
    exit(0)
    """)
    compile_gpu.write(script_path=source_path + '/compile_gpu.m')

    script = """
    #!/bin/bash
    set -e

    cd {source_path}
    matlab -nodisplay -nosplash -r "compile_gpu"
    """.format(source_path=source_path)
    ss = mlpr.ShellScript(script=script)
    ss.start()
    retcode = ss.wait()
    if retcode != 0:
        raise Exception('Compute gpu script returned a non-zero exit code.')

    # The dir hash method does not seem to be working for some reason here
    # hash0 = mt.computeDirHash(source_path)
    # mt.setValue(key=key, value=hash0)
    mt.saveObject(object=key, dest_path=source_path + '/spikeforest.json')

    return source_path
