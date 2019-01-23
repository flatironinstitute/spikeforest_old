import types
import types
import hashlib
import json
import os
import shutil
import tempfile
from pairio import client as pairio
from kbucket import client as kbucket
import inspect
from subprocess import Popen, PIPE
import shlex

def sha1(str):
    hash_object = hashlib.sha1(str.encode('utf-8'))
    return hash_object.hexdigest()
        
def compute_job_input_signature(val,input_name,*,directory):
    if type(val)==str:
        if val.startswith('sha1://'):
            if directory:
                raise Exception('sha1:// path not allowed for directory input')
            list=str.split(val,'/')
            return list[2]
        elif val.startswith('kbucket://'):
            if directory:
                hash0=kbucket.computeDirHash(val)
                if not hash0:
                    raise Exception('Unable to compute directory hash for input: {}'.format(input_name))
                return hash0
            else:
                sha1=kbucket.computeFileSha1(val)
                if not sha1:
                    raise Exception('Unable to compute file sha-1 for input: {}'.format(input_name))
                return sha1
        else:
            if os.path.exists(val):
                if directory:
                    if os.path.isdir(val):
                        hash0=kbucket.computeDirHash(val)
                        if not hash0:
                            raise Exception('Unable to compute hash for directory input: {} ({})'.format(input_name,val))
                        return hash0
                    else:
                        raise Exception('Input is not a directory: {}'.format(input_name))
                else:
                    if os.path.isfile(val):
                        sha1=kbucket.computeFileSha1(val)
                        if not sha1:
                            raise Exception('Unable to compute sha-1 of input: {} ({})'.format(input_name,val))        
                        return sha1
                    else:
                        raise Exception('Input is not a file: {}'.format(input_name))
            else:
                raise Exception('Input file does not exist: '+val)    
    else:
        if hasattr(val,'signature'):
            return getattr(val,'signature')
        else:
            raise Exception("Unable to compute signature for input: {}".format(input_name))
            
def get_file_extension(fname):
    if type(fname)==str:
        name, ext = os.path.splitext(fname)
        return ext
    else:
        return ''
    
def compute_processor_job_output_signature(self,output_name):
    processor_inputs=[]
    job_inputs=[]
    for input0 in self.INPUTS:
        name0=input0.name
        val0=getattr(self,name0)
        processor_inputs.append(dict(
            name=name0
        ))
        job_inputs.append(dict(
            name=name0,
            signature=compute_job_input_signature(val0,input_name=name0,directory=input0.directory),
            ext=get_file_extension(val0)
        ))
    processor_outputs=[]
    job_outputs=[]
    for output0 in self.OUTPUTS:
        name0=output0.name
        processor_outputs.append(dict(
            name=name0
        ))
        val0=getattr(self,name0)
        if type(val0)==str:
            job_outputs.append(dict(
                name=name0,
                ext=get_file_extension(val0)
            ))
        else:
            job_outputs.append(dict(
                name=name0,
                ext=val0['ext']
            ))
    processor_parameters=[]
    job_parameters=[]
    for param0 in self.PARAMETERS:
        name0=param0.name
        processor_parameters.append(dict(
            name=name0
        ))
        job_parameters.append(dict(
            name=name0,
            value=getattr(self,name0)
        ))
    processor_obj=dict(
        processor_name=self.NAME,
        processor_version=self.VERSION,
        inputs=processor_inputs,
        outputs=processor_outputs,
        parameters=processor_parameters
    )
    signature_obj=dict(
        processor=processor_obj,
        inputs=job_inputs,
        outputs=job_outputs,
        parameters=job_parameters
    )
    if output_name:
        signature_obj["output_name"]=output_name
    signature_string=json.dumps(signature_obj, sort_keys=True)
    return sha1(signature_string)

def create_temporary_file(fname):
    tempdir=os.environ.get('KBUCKET_CACHE_DIR',tempfile.gettempdir())
    tmp=tempdir+'/mlprocessors'
    if not os.path.exists(tmp):
        os.mkdir(tmp)
    return tmp+'/'+fname

class ProcessorExecuteOutput():
    def __init__(self):
        self.outputs=dict()

def _read_text_file(fname):
    with open(fname) as f:
        return f.read()
    
def _write_text_file(fname,str):
    with open(fname,'w') as f:
        f.write(str)

def _read_text_file(fname):
    with open(fname) as f:
        return f.read()
    
def _write_text_file(fname,str):
    with open(fname,'w') as f:
        f.write(str)

def _execute_in_container(proc, X, *, container, tempdir, **kwargs):
    singularity_opts=[]
    kbucket_cache_dir=kbucket.getConfig()['local_cache_dir']
    singularity_opts.append('-B {}:{}'.format(kbucket_cache_dir,'/sha1-cache'))
    singularity_opts.append('-B /tmp:/tmp')

    for input0 in proc.INPUTS:
        name0=input0.name
        fname0=getattr(X,name0)
        if fname0:
            if fname0.startswith('kbucket://') or fname0.startswith('sha1://'):
                pass
            else:
                fname0=os.path.abspath(fname0)
                fname2='/execute_in_container/input_{}'.format(name0)
                kwargs[name0]=fname2
                singularity_opts.append('-B {}:{}'.format(fname0,fname2))
                
    for output0 in proc.OUTPUTS:
        name0=output0.name
        val=getattr(X,name0)
        if val:
            val=os.path.abspath(val)
            dirname=os.path.dirname(val)
            filename=os.path.basename(val)
            dirname2='/execute_in_container/outputdir_{}'.format(name0)
            kwargs[name0]=dirname2+'/'+filename
            singularity_opts.append('-B {}:{}'.format(dirname,dirname2))

    expanded_kwargs_list=[]
    for key in kwargs:
        val=kwargs[key]
        if type(val)==str:
            val="'{}'".format(val)
        expanded_kwargs_list.append('{}={}'.format(key,val))
    expanded_kwargs=', '.join(expanded_kwargs_list)

    processor_source_fname=inspect.getsourcefile(proc)
    processor_source_dirname=os.path.dirname(processor_source_fname)
    processor_source_basename=os.path.basename(processor_source_fname)
    processor_source_basename_noext=os.path.splitext(processor_source_basename)[0]
    if not processor_source_fname:
        raise Exception('inspect.getsourcefile() returned empty for processor.')
    singularity_opts.append('-B {}:/execute_in_container/processor_source'.format(processor_source_dirname))

    # Code generation
    code="""
from processor_source.{processor_source_basename_noext} import {processor_name}

def main():
    {processor_name}.execute({expanded_kwargs})

if __name__ == "__main__":
    main()
    """
    code=code.replace('{processor_source_basename_noext}',processor_source_basename_noext)
    code=code.replace('{processor_name}',proc.__name__)
    code=code.replace('{expanded_kwargs}',expanded_kwargs)

    _write_text_file(tempdir+'/execute_in_container.py',code)
    singularity_opts.append('-B {}:/execute_in_container/execute_in_container.py'.format(tempdir+'/execute_in_container.py'))

    env_vars=[]
    if getattr(proc,'ENVIRONMENT_VARIABLES'):
        list=proc.ENVIRONMENT_VARIABLES
        for v in list:
            val=os.environ.get(v,'')
            if val:
                env_vars.append('{}={}'.format(v,val))
    singularity_cmd='singularity exec --contain -e {} {} bash -c "KBUCKET_CACHE_DIR=/sha1-cache {} python /execute_in_container/execute_in_container.py"'.format(' '.join(singularity_opts),container,' '.join(env_vars))


    retcode = _run_command_and_print_output(singularity_cmd)
    if retcode != 0:
        raise Exception('Processor in singularity returned a non-zero exit code')

def _run_command_and_print_output(command):
    print('RUNNING: '+command)
    with Popen(shlex.split(command), stdout=PIPE, stderr=PIPE) as process:
        while True:
            output_stdout = process.stdout.readline()
            output_stderr = process.stderr.readline()
            if (not output_stdout) and (not output_stderr) and (process.poll() is not None):
                break
            if output_stdout:
                print(output_stdout.decode())
            if output_stderr:
                print(output_stderr.decode())
        rc = process.poll()
        return rc

def execute(proc, _cache=True, _force_run=None, _container=None, **kwargs):

    if _force_run is None:
        if os.environ.get('MLPROCESSORS_FORCE_RUN','') == 'TRUE':
            _force_run=True
        else:
            _force_run=False

    # Execute a processor
    print ('::::::::::::::::::::::::::::: '+proc.NAME)
    X=proc() # instance
    ret=ProcessorExecuteOutput() # We will return this object
    for input0 in proc.INPUTS:
        name0=input0.name
        if not name0 in kwargs:
            raise Exception('Missing input: {}'.format(name0))
        setattr(X,name0,kwargs[name0])
    for output0 in proc.OUTPUTS:
        name0=output0.name
        if not name0 in kwargs:
            raise Exception('Missing output: {}'.format(name0))
        setattr(X,name0,kwargs[name0])
    for param0 in proc.PARAMETERS:
        name0=param0.name
        if not name0 in kwargs:
            if param0.optional:
                val0=param0.default
            else:
                raise Exception('Missing required parameter: {}'.format(name0))
        else:
            val0=kwargs[name0]
        setattr(X,name0,val0)
    if _cache:
        outputs_all_in_pairio=True
        output_signatures=dict()
        output_sha1s=dict()
        cache_collections=set()
        for output0 in proc.OUTPUTS:
            name0=output0.name
            signature0=compute_processor_job_output_signature(X,name0)
            output_signatures[name0]=signature0
            output_sha1,output_collection=pairio.get(signature0,return_collection=True)
            if output_sha1 is not None:
                print ('Found output "{}" in cache collection: {}'.format(name0,output_collection))
                cache_collections.add(output_collection)
                output_sha1s[name0]=output_sha1

                # Do the following because if we have it locally,
                # we want to make sure it also gets propagated remotely
                # and vice versa
                pairio.set(signature0,output_sha1)
            else:
                outputs_all_in_pairio=False
        output_files_all_found=False
        output_files=dict()
        if outputs_all_in_pairio:
            output_files_all_found=True
            for output0 in proc.OUTPUTS:
                out0=getattr(X,name0)
                if out0:
                    name0=output0.name
                    ext0=_get_output_ext(out0)
                    sha1=output_sha1s[name0]
                    output_files[name0]='sha1://'+sha1+'/'+name0+ext0
                    fname=kbucket.findFile(sha1=sha1)
                    if not fname:
                        output_files_all_found=False
        if outputs_all_in_pairio and (not output_files_all_found):
            print ('Found job in cache, but not all output files exist.')

        if output_files_all_found:
            if not _force_run:
                print ('Using outputs from cache:',','.join(list(cache_collections)))
                for output0 in proc.OUTPUTS:
                    name0=output0.name
                    fname1=output_files[name0]
                    fname2=getattr(X,name0)
                    if type(fname2)==str:
                        fname1=kbucket.realizeFile(fname1)
                        if fname1!=fname2:
                            if os.path.exists(fname2):
                                os.remove(fname2)
                            shutil.copyfile(fname1,fname2)
                        ret.outputs[name0]=fname2
                    else:
                        ret.outputs[name0]=fname1
                return ret
            else:
                print ('Found outputs in cache, but forcing run...')

    for input0 in proc.INPUTS:
        name0=input0.name
        if hasattr(X,name0):
            val0=getattr(X,name0)
            if input0.directory:
                val1=val0
            else:
                val1=kbucket.realizeFile(val0)
                if not val1:
                    raise Exception('Unable to realize input file {}: {}'.format(name0,val0))
            setattr(X,name0,val1)
        
    temporary_output_files=set()
    for output0 in proc.OUTPUTS:
        name0=output0.name
        val0=getattr(X,name0)
        job_signature0=compute_processor_job_output_signature(X,None)
        if type(val0)!=str:
            fname0=job_signature0+'_'+name0+val0['ext']
            tmp_fname=create_temporary_file(fname0)
            temporary_output_files.add(tmp_fname)
            setattr(X,name0,tmp_fname)
    ## Now it is time to execute
    if not _container:
        try:
            print ('MLPR EXECUTING::::::::::::::::::::::::::::: '+proc.NAME)
            X.run()
            print ('MLPR FINISHED ::::::::::::::::::::::::::::: '+proc.NAME)
        except:
            # clean up temporary output files
            print ('Problem executing {}. Cleaning up files.'.format(proc.NAME))
            for fname in temporary_output_files:
                if os.path.exists(fname):
                    os.remove(fname)
            raise
    else:
        ## in a container
        tempdir=tempfile.mkdtemp()
        try:
            _execute_in_container(proc, X, container=_container, tempdir=tempdir, **kwargs)
        except:
            shutil.rmtree(tempdir)
            raise
        shutil.rmtree(tempdir)
    
    for output0 in proc.OUTPUTS:
        name0=output0.name
        output_fname=getattr(X,name0)
        if output_fname in temporary_output_files:
            output_fname=kbucket.moveFileToCache(output_fname)
        ret.outputs[name0]=output_fname
        if _cache:
            output_sha1=kbucket.computeFileSha1(output_fname)
            signature0=output_signatures[name0]
            pairio.set(signature0,output_sha1)

    return ret

def _get_output_ext(out0):
    if type(out0)==str:
        filename, ext = os.path.splitext(out0)
        return ext
    elif type(out0)==dict:
        if 'ext' in out0:
            return out0['ext']
    return ''