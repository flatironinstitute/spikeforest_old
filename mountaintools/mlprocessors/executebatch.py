import os
import multiprocessing
import tempfile
import shutil
from mountaintools import client as ca
from .execute import ProcessorExecuteOutput

# module global
_realized_files = set()
_compute_resources_config = dict()

def configComputeResource(name, *, resource_name, collection, share_id):
    if resource_name is not None:
        _compute_resources_config[name]=dict(
            resource_name=resource_name,
            collection=collection,
            share_id=share_id
        )
    else:
        _compute_resources_config[name] = None

def executeBatch(*, jobs, label='', num_workers=None, compute_resource=None, batch_name=None):
    if type(compute_resource)==str:
        if compute_resource in _compute_resources_config:
            compute_resource=_compute_resources_config[compute_resource]
        else:
            raise Exception('No compute resource named {}. Use mlprocessors.configComputeResource("{}",...).'.format(compute_resource, compute_resource))

    if type(compute_resource)==dict:
        if compute_resource['resource_name'] is None:
            compute_resource = None

    # make sure the files to realize are absolute paths
    for job in jobs:
        if 'processor_name' in job:
            if 'files_to_realize' in job:
                for i, fname in enumerate(job['files_to_realize']):
                    if fname.startswith('kbucket://') or fname.startswith('sha1://'):
                        pass
                    else:
                        fname = os.path.abspath(fname)
                    job['files_to_realize'][i] = fname
            for name0, output0 in job['outputs'].items():
                if type(output0)==dict:
                    if 'dest_path' in output0:
                        if compute_resource is not None:
                            # In this case we are going to need to realize the file
                            output0['upload'] = True

    if compute_resource is None:
        _realize_required_files_for_jobs(jobs=jobs, cairio_client=ca, realize_code=False)

    if len(jobs)>0:
        if num_workers is not None:
            if compute_resource is not None:
                raise Exception('Cannot specify both num_workers and compute_resource.')
            pool = multiprocessing.Pool(num_workers)
            results = pool.map(executeJob, jobs)
            pool.close()
            pool.join()
            for i, job in enumerate(jobs):
                job['result'] = results[i]
        else:
            if compute_resource is not None:
                if type(compute_resource)==dict:
                    from .computeresourceclient import ComputeResourceClient
                    CRC=ComputeResourceClient(**compute_resource)
                    batch_id = CRC.initializeBatch(jobs=jobs, label=label)
                    CRC.startBatch(batch_id=batch_id)
                    try:
                        CRC.monitorBatch(batch_id=batch_id)
                    except:
                        CRC.stopBatch(batch_id=batch_id)
                        raise

                    results0 = CRC.getBatchJobResults(batch_id=batch_id)
                    if results0 is None:
                        raise Exception('Unable to get batch results.')
                    for i, job in enumerate(jobs):
                        result0 = results0['results'][i]['result']
                        if result0 is None:
                            raise Exception('Unable to find result for job.')
                        job['result'] = result0
                    
                else:
                    raise Exception('Compute resource must be a dict.')
            else:
                for job in jobs:
                    job['result'] = executeJob(job)

    ret=[]
    for job in jobs:
        if 'processor_name' in job:
            results0=job['result']
            result_outputs0=results0.get('outputs', None)
            print(job)
            if results0['retcode']==0:
                for name0, output0 in job['outputs'].items():
                    if name0 not in result_outputs0:
                        raise Exception('Unexpected: result not found {}'.format(name0))
                    result_output0=result_outputs0[name0]
                    if type(output0)==dict:
                        if 'dest_path' in output0:
                            dest_path0=output0['dest_path']
                            print('Saving output {} --> {}'.format(name0,dest_path0))
                            ca.realizeFile(path=result_output0, dest_path=dest_path0)
                        if compute_resource is None:
                            if output0.get('upload', False):
                                ca.saveFile(path=result_output0)
            RR=ProcessorExecuteOutput()
            RR.outputs=result_outputs0
            RR.stats=results0['stats']
            RR.retcode=results0['retcode']
            if results0['console_out']:
                RR.console_out=ca.loadText(path=results0['console_out'])
            else:
                RR.console_out=None
            ret.append(RR)
        else:
            RR=ProcessorExecuteOutput()
            ret.append(RR)
    return ret

def executeJob(job, cairio_client=ca):
    if 'processor_name' not in job:
        # a null job
        return dict()
    tempdir = tempfile.mkdtemp()
    keep_temp_files = job.get('_keep_temp_files', None)
    try:
        processor_code = cairio_client.loadObject(path=job['processor_code'])
        if processor_code is None:
            raise Exception('Unable to load processor code for job: '+job['processor_code'])
        _write_python_code_to_directory(
            tempdir+'/processor_source', processor_code)

        processor_class_name = job['processor_class_name']

        container = job.get('container', None)
        if container:
            container = cairio_client.realizeFile(path=container)

        execute_kwargs = dict(
            _cache=job.get('_cache', None),
            _force_run=job.get('_force_run', None),
            _keep_temp_files=keep_temp_files,
            _container=container,
        )
        for key in job['inputs']:
            execute_kwargs[key] = job['inputs'][key]
        temporary_output_files = dict()
        for key in job['outputs']:
            out0 = job['outputs'][key]
            tmp_fname = tempdir+'/output_'+key+out0['ext']
            temporary_output_files[key] = tmp_fname
            execute_kwargs[key] = tmp_fname
        for key in job['parameters']:
            execute_kwargs[key] = job['parameters'][key]
        temporary_output_files['_stats_out']=tempdir+'/_stats.json'
        execute_kwargs['_stats_out']=temporary_output_files['_stats_out']
        temporary_output_files['_console_out']=tempdir+'/_console_out.txt'
        execute_kwargs['_console_out']=temporary_output_files['_console_out']
        temporary_output_files['_output_signatures_out']=tempdir+'/_output_signatures_out.json'
        execute_kwargs['_output_signatures_out']=temporary_output_files['_output_signatures_out']
        expanded_execute_kwargs = _get_expanded_args(execute_kwargs)

        # Code generation
        code = """
from processor_source import {processor_class_name}

def main():
    {processor_class_name}.execute({expanded_execute_kwargs})

if __name__ == "__main__":
    main()
        """
        code = code.replace('{processor_class_name}', processor_class_name)
        code = code.replace('{expanded_execute_kwargs}',
                            expanded_execute_kwargs)

        _write_text_file(tempdir+'/execute.py', code)

        #retcode, _unused_console_out = _run_command_and_print_output(
        #    'python3 {}/execute.py'.format(tempdir))
        env=os.environ
        subprocess.call('python3 {}/execute.py'.format(tempdir),shell=True,env=env)

        console_out=cairio_client.loadText(path=temporary_output_files['_console_out'])
        stats_out=cairio_client.loadObject(path=temporary_output_files['_stats_out'])
        output_signatures=cairio_client.loadObject(path=temporary_output_files['_output_signatures_out'])

        if stats_out:
            retcode=stats_out['retcode']
        else:
            retcode=-3
        ret = dict(
            retcode=retcode,
            outputs=dict(),
            stats=stats_out,
            console_out=cairio_client.saveText(console_out),
            output_signatures=output_signatures
        )
        if console_out:
            ret['console_out']=cairio_client.saveText(console_out)
        else:
            ret['console_out']=None
        
        if retcode==0:
            for key in job['outputs']:
                out0 = job['outputs'][key]
                if out0.get('upload', False):
                    ret['outputs'][key] = ca.saveFile(
                        temporary_output_files[key], basename=key+out0['ext'])
                else:
                    ret['outputs'][key] = 'sha1://' + \
                        cairio_client.computeFileSha1(
                            temporary_output_files[key])+'/'+key+out0['ext']
        return ret
    except:
        if not keep_temp_files:
            shutil.rmtree(tempdir)
        raise
    if not keep_temp_files:
        shutil.rmtree(tempdir)
    return ret

def _realize_required_files_for_jobs(*, cairio_client, jobs, realize_code=False):
    containers_to_realize=set()
    code_to_realize=set()
    files_to_realize=set()
    for job in jobs:
        container0 = job.get('container', None)
        if container0 is not None:
            containers_to_realize.add(container0)
        files_to_realize0 = job.get('files_to_realize', [])
        for f0 in files_to_realize0:
            files_to_realize.add(f0)
        code0 = job.get('processor_code', None)
        if code0 is not None:
            code_to_realize.add(code0)
    if len(containers_to_realize)>0:
        print('Realizing {} containers...'.format(len(containers_to_realize)))
        _realize_files(containers_to_realize, cairio_client=cairio_client)
    if len(files_to_realize)>0:
        print('Realizing {} files...'.format(len(files_to_realize)))
        _realize_files(files_to_realize, cairio_client=cairio_client)
    if realize_code:
        if len(code_to_realize)>0:
            print('Realizing {} code objects...'.format(len(code_to_realize)))
            _realize_files(code_to_realize, cairio_client=cairio_client)

def _realize_files(files, *, cairio_client):
    for file0 in files:
        if file0 not in _realized_files:
            print('Realizing file and ensuring in local cache: '+file0)
            a=cairio_client.realizeFile(file0)
            print(a)
            b=cairio_client.copyToLocalCache(path=a)
            print(b)
            if b:
                _realized_files.add(file0)
            else:
                raise Exception('Unable to realize file: '+file0)