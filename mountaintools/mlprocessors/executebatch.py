import os
import json
import multiprocessing
import random
import time
from mountainclient import client as mt
from mountainclient import MountainClient
from .computeresourceclient import ComputeResourceClient
from .shellscript import ShellScript
from .temporarydirectory import TemporaryDirectory
from .mountainjob import MountainJob
from .mountainjob import MountainJobResult
import mtlogging
from copy import deepcopy

# module global
_realized_files = set()
_compute_resources_config = dict()

def configComputeResource(name, *, resource_name, collection=None, kachery_name=None, share_id=None):
    if share_id is not None:
        print('WARNING: use kachery_name in configComputeResource (share_id) is deprecated)')
        assert kachery_name is None
        kachery_name = share_id
    if resource_name is not None:
        _compute_resources_config[name]=dict(
            resource_name=resource_name,
            collection=collection,
            kachery_name=kachery_name
        )
    else:
        _compute_resources_config[name] = None

@mtlogging.log()
def executeBatch(*, jobs, label='', num_workers=None, compute_resource=None, halt_key=None, job_status_key=None, job_result_key=None, srun_opts=None, job_index_file=None, cached_results_only=False):
    all_kwargs = locals()

    if len(jobs) == 0:
        return []

    if num_workers == 1:
        num_workers = None
    if not srun_opts:
        srun_opts = None

    if num_workers is not None:
        if compute_resource is not None:
            raise Exception('Cannot specify both num_workers and compute_resource in executeBatch.')
        if job_index_file is not None:
            raise Exception('Cannot specify both num_workers and job_index_file in executeBatch.')
    if compute_resource is not None:
        if srun_opts is not None:
            raise Exception('Cannot specify both compute_resource and srun_opts in executeBatch.')
        if job_index_file is not None:
            raise Exception('Cannot specify both compute_resource and job_index_file in executeBatch.')
    if srun_opts is not None:
        if job_index_file is not None:
            raise Exception('Cannot specify both srun_opts and job_index_file in executeBatch.')

    if type(compute_resource)==str:
        if compute_resource in _compute_resources_config:
            compute_resource=_compute_resources_config[compute_resource]
        else:
            raise Exception('No compute resource named {}. Use mlprocessors.configComputeResource("{}",...).'.format(compute_resource, compute_resource))

    if type(compute_resource)==dict:
        if compute_resource['resource_name'] is None:
            compute_resource = None

    if compute_resource or srun_opts:
        if compute_resource:
            mtlogging.sublog('checking-for-cached-results-prior-to-sending-to-compute-resource')
            print('Checking for cached results prior to sending to compute resource...')
        elif srun_opts:
            mtlogging.sublog('checking-for-cached-results-prior-to-using-srun')
            print('Checking for cached results prior to using srun...')
        kwargs0 = all_kwargs
        kwargs0['compute_resource'] = None
        kwargs0['cached_results_only'] = True
        kwargs0['num_workers'] = 10 # check it in parallel
        kwargs0['srun_opts'] = None
        results0 = executeBatch(**kwargs0)
        all_complete = True
        num_found = 0
        for ii, job in enumerate(jobs):
            if results0[ii]:
                num_found = num_found+1
                job.result = results0[ii]
            else:
                all_complete = False
        if num_found > 0:
            print('Found {} of {} cached results'.format(num_found, len(jobs)))
        if all_complete:
            return results0
        mtlogging.sublog(None)

    jobs2 = [job for job in jobs if (not job.result)]

    if compute_resource:
        for job in jobs2:
            job.useRemoteUrlsForInputFiles()

    files_to_realize = []
    for job in jobs2:
        files_to_realize.extend(job.getFilesToRealize())
    files_to_realize = list(set(files_to_realize))

    local_client = MountainClient()

    if compute_resource:
        # print('Ensuring files are available on remote server...')
        # mtlogging.sublog('ensuring-files-remote')
        # collection=compute_resource.get('collection', None)
        # upload_to=compute_resource.get('kachery_name', None)
        # for fname in files_to_realize:
        #     if fname.startswith('sha1://'):
        #         if local_client.findFile(path=fname):
        #             mt.saveFile(path=fname, collection=collection, upload_to=upload_to)
        #     elif fname.startswith('kbucket://') or fname.startswith('sha1dir://'):
        #         # todo: in case of sha1dir, save the dir
        #         pass
        #     else:
        #         mt.saveFile(path=fname, collection=collection, upload_to=upload_to)

        mtlogging.sublog('initializing-batch')

        args = deepcopy(compute_resource)
        if 'share_id' in args:
            args['kachery_name'] = args['share_id']
            del args['share_id']
        CRC=ComputeResourceClient(**args)

        batch_id = CRC.initializeBatch(jobs=jobs2, label=label)
        CRC.startBatch(batch_id=batch_id)
        mtlogging.sublog('running-batch')
        try:
            CRC.monitorBatch(batch_id=batch_id, jobs=jobs2, label=label)
        except:
            CRC.stopBatch(batch_id=batch_id)
            raise

        mtlogging.sublog('getting-batch-results')
        results = CRC.getBatchJobResults(batch_id=batch_id)
        if results is None:
            raise Exception('Unable to get batch results.')
        for i, job2 in enumerate(jobs2):
            result0 = results[i]
            if result0:
                job2.result = result0
            else:
                raise Exception('Unexpected: Unable to find result for job {}'.format(i))

        mtlogging.sublog('realizing-outputs')
        # Download outputs to local computer
        download_from=compute_resource.get('kachery_name', None)
        for ii, result in enumerate(results):
            if result and (result.retcode == 0):
                for output_name, output_path in result.outputs.items():
                    if not local_client.realizeFile(path=output_path):
                        print('Downloading output {} {} ...'.format(output_name, output_path))
                        local_path = mt.realizeFile(path=output_path, download_from=download_from)
                        if not local_path:
                            raise Exception('Unable to realize output {} from {}'.format(output_name, output_path))
                if not local_client.realizeFile(path=result.console_out):
                    print('Downloading console output {}...'.format(result.console_out))
                    local_path = mt.realizeFile(path=result.console_out, download_from=download_from)
                    if not local_path:
                        raise Exception('Unable to realize console output from {}'.format(output_name))
                
                

        mtlogging.sublog('caching-results-locally')
        # save results to local cache
        for ii, result in enumerate(results):
            if result and (result.retcode == 0):
                jobs2[ii].storeResultInCache(result)
            
        return [job.result for job in jobs]

    # Not using compute resource, do this locally
    if not cached_results_only:
        mtlogging.sublog('realizing-files')
        if job_index_file is None:
            print('Making sure files are available on local computer...')
            for fname in files_to_realize:
                print('Realizing {}...'.format(fname))
                mt.realizeFile(path=fname)
        mtlogging.sublog(None)

    if srun_opts is None:
        for job_index, job in enumerate(jobs2):
            setattr(job, 'halt_key', halt_key)
            setattr(job, 'job_status_key', job_status_key)
            setattr(job, 'job_index', job_index)
            setattr(job, 'job_result_key', job_result_key)
            job.setUseCachedResultsOnly(cached_results_only)

        if num_workers is not None:
            pool = multiprocessing.Pool(num_workers)
            results2 = pool.map(_execute_job, jobs2)
            pool.close()
            pool.join()
        else:
            results2 = []
            if job_index_file is None:
                for job in jobs2:
                    results2.append(_execute_job(job))
            else:
                while True:
                    job_index = _take_next_batch_job_index_to_run(job_index_file)
                    if job_index < len(jobs2):
                        print('Executing job {}'.format(job_index))
                        _execute_job(jobs2[job_index])
                    else:
                        break
                return None
                    
        for i, job in enumerate(jobs2):
            job.result = results2[i]
    else:
        # using srun
        keep_temp_files = True
        with TemporaryDirectory(remove=(not keep_temp_files)) as temp_path:
            local_client = MountainClient()
            job_objects = [job.getObject() for job in jobs2]
            jobs_path=os.path.join(temp_path, 'jobs.json')
            job_index_file=os.path.join(temp_path, 'job_index.txt')
            with open(job_index_file, 'w') as f:
                f.write('0')
            local_client.saveObject(object=job_objects, dest_path=jobs_path)
            if job_result_key is None:
                job_result_key = dict(
                    name='executebatch_job_result',
                    randid=_random_string(8)
                )
            srun_py_script = ShellScript("""
                #!/usr/bin/env python

                from mlprocessors import executeBatch
                from mountaintools import MountainClient
                from mlprocessors import MountainJob

                local_client = MountainClient()

                job_objects = local_client.loadObject(path = '{jobs_path}')
                jobs = [MountainJob(job_object=obj) for obj in job_objects]

                executeBatch(jobs=jobs, label='{label}', num_workers=None, compute_resource=None, halt_key={halt_key}, job_status_key={job_status_key}, job_result_key={job_result_key}, srun_opts=None, job_index_file='{job_index_file}', cached_results_only={cached_results_only})
            """, script_path=os.path.join(temp_path, 'execute_batch_srun.py'), keep_temp_files=keep_temp_files)
            srun_py_script.substitute('{jobs_path}', jobs_path)
            srun_py_script.substitute('{label}', label)
            if halt_key:
                srun_py_script.substitute('{halt_key}', json.dumps(halt_key))
            else:
                srun_py_script.substitute('{halt_key}', 'None')
            if job_status_key:
                srun_py_script.substitute('{job_status_key}', json.dumps(job_status_key))
            else:
                srun_py_script.substitute('{job_status_key}', 'None')
            if job_result_key:
                srun_py_script.substitute('{job_result_key}', json.dumps(job_result_key))
            else:
                srun_py_script.substitute('{job_result_key}', 'None')
            srun_py_script.substitute('{cached_results_only}', str(cached_results_only))
            srun_py_script.substitute('{job_index_file}', job_index_file)
            srun_py_script.write()

            srun_opts_adjusted, num_workers_adjusted = _adjust_srun_opts_for_num_jobs(srun_opts, num_workers or 1, len(jobs2))

            print('USING SRUN OPTS: {}'.format(srun_opts_adjusted))
            print('USING NUM SIMULTANEOUS SRUN CALLS: {}'.format(num_workers_adjusted))

            srun_sh_scripts = []
            for ii in range(num_workers_adjusted):
                if srun_opts is not 'fake':
                    srun_sh_script = ShellScript("""
                        #!/bin/bash
                        set -e

                        srun {srun_opts} {srun_py_script}
                    """, keep_temp_files=keep_temp_files)
                else:
                    srun_sh_script = ShellScript("""
                        #!/bin/bash
                        set -e

                        {srun_py_script}
                    """, keep_temp_files=keep_temp_files)
                srun_sh_script.substitute('{srun_opts}', srun_opts_adjusted)
                srun_sh_script.substitute('{srun_py_script}', srun_py_script.scriptPath())
                srun_sh_scripts.append(srun_sh_script)
            
            for srun_sh_script in srun_sh_scripts:
                srun_sh_script.start()
            for srun_sh_script in srun_sh_scripts:
                while srun_sh_script.isRunning():
                    srun_sh_script.wait(5)
                if srun_sh_script.returnCode() != 0:
                    print('Non-zero return code for srun script. Stopping scripts...')
                    for srun_sh_script in srun_sh_scripts:
                        srun_sh_script.stop()
                    raise Exception('Non-zero return code for srun script.')
            
            result_objects=[]
            for ii, job in enumerate(jobs2):
                print('Loading result object...', job_result_key, str(ii))
                num_tries = 0
                while True:
                    result_object = local_client.loadObject(key=job_result_key, subkey=str(ii))
                    if (result_object is None) and (not cached_results_only):
                        print('Problem loading result....', job_result_key, str(ii))
                        print('=====================', local_client.getValue(key=job_result_key, subkey='-'))
                        print('=====================', local_client.getValue(key=job_result_key, subkey=str(ii)))
                        num_tries = num_tries + 1
                        if num_tries>=3:
                            raise Exception('Unable to load result object after {} tries.')
                        print('Retrying...')
                        time.sleep(1)
                    else:
                        print('Loaded result object...', job_result_key, str(ii))
                        break
                result_objects.append(result_object)
            results2 = [MountainJobResult(result_object=obj) for obj in result_objects]
            for i, job in enumerate(jobs2):
                job.result = results2[i]

    return [job.result for job in jobs]

def _take_next_batch_job_index_to_run(job_index_file):
    while True:
        time.sleep(random.uniform(0, 0.1))
        fname2=_attempt_lock_file(job_index_file)
        if fname2:
            index=int(_read_text_file(fname2))
            _write_text_file(fname2,'{}'.format(index+1))
            os.rename(fname2,job_index_file) # put it back
            return index

def _attempt_lock_file(fname):
    if os.path.exists(fname):
        fname2=fname+'.lock.'+_random_string(6)
        try:
            os.rename(fname, fname2)
        except:
            return False
        if os.path.exists(fname2):
            return fname2

def _set_job_status(job, status):
    local_client = MountainClient()
    job_status_key = getattr(job, 'job_status_key', None)
    job_index = getattr(job, 'job_index', None)
    if job_status_key:
        subkey = str(job_index)
        local_client.setValue(key=job_status_key, subkey=subkey, value=status)

def _set_job_result(job, result_object):
    local_client = MountainClient()
    job_result_key = getattr(job, 'job_result_key', None)
    job_index = getattr(job, 'job_index', None)
    if job_result_key:
        subkey = str(job_index)
        num_tries=0
        while True:
            print('Saving result object...')
            local_client.saveObject(key=job_result_key, subkey=subkey, object=result_object)
            testing = local_client.loadObject(key=job_result_key, subkey=subkey)
            if result_object and (testing is None):
                print('WARNING: Problem loading object immediately after saving....')
                print('==== value', local_client.getValue(key=job_result_key, subkey=subkey))
                print('==== object', local_client.loadObject(key=job_result_key, subkey=subkey))
                print(result_object)
                num_tries = num_tries + 1
                if num_tries >= 3:
                    raise Exception('Unexpected: Problem loading object immediately after saving')
                else:
                    print('retrying...')
            else:
                # we are good
                break

@mtlogging.log()
def _execute_job(job):
    local_client = MountainClient()
    halt_key = getattr(job, 'halt_key', None)
    if halt_key:
        halt_val = local_client.getValue(key=halt_key)
        if halt_val:
            raise Exception('Batch halted.')
    
    _set_job_status(job, 'running')

    result = job.execute()

    if result:
        if result.retcode == 0:
            _set_job_status(job, 'finished')
        else:
            _set_job_status(job, 'error')
        _set_job_result(job, result.getObject())
    else:
        _set_job_status(job, 'result-not-found')

    return result

def _adjust_srun_opts_for_num_jobs(srun_opts, num_workers, num_jobs):
    vals = srun_opts.split()
    for i in range(len(vals)):
        if vals[i] == '-n' and (i+1<len(vals)):
            nval = int(vals[i+1])
            if num_jobs <= nval:
                nval = num_jobs
                num_workers = 1
            elif num_jobs <= nval * (num_workers-1):
                num_workers = int((num_jobs-1)/nval) + 1
            vals[i+1] = str(nval)
    return ' '.join(vals), num_workers

def _random_string(num_chars):
    chars = 'abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789'
    return ''.join(random.choice(chars) for _ in range(num_chars))

def _write_text_file(fname,txt):
    with open(fname,'w') as f:
        f.write(txt)

def _read_text_file(fname):
    with open(fname,'r') as f:
        return f.read()