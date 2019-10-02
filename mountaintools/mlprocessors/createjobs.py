import mtlogging
import os
import fnmatch
from mountainclient import MountainClient
from .mountainjob import MountainJob
import json
import inspect
import multiprocessing
from typing import Optional, List

local_client = MountainClient()


@mtlogging.log()
def createJobs(proc, argslist, verbose=None) -> List[MountainJob]:
    if verbose is None:
        verbose = True
    # Get the code for the processor
    try:
        processor_source_fname = os.path.abspath(inspect.getsourcefile(proc))
    except:
        print('Warning: Unable to get source file for processor {}. You will not be able to run this on a cluster or in a container.'.format(proc.NAME))
        processor_source_fname = None
    if processor_source_fname is not None:
        processor_source_dirname = os.path.dirname(processor_source_fname)
        processor_source_basename = os.path.basename(processor_source_fname)
        processor_source_basename_noext = os.path.splitext(processor_source_basename)[0]
        code = _read_python_code_of_directory(
            processor_source_dirname,
            additional_files=getattr(proc, 'ADDITIONAL_FILES', []),
            exclude_init=True
        )
        code['files'].append(dict(
            name='__init__.py',
            content='from .{} import {}'.format(
                processor_source_basename_noext, proc.__name__)
        ))
        if hasattr(proc, 'LOCAL_MODULES'):
            code['dirs'].append(dict(
                name='_local_modules',
                content=dict(
                    files=[],
                    dirs=[
                        dict(
                            name=os.path.basename(local_module_path),
                            content=_read_python_code_of_directory(os.path.join(processor_source_dirname, local_module_path), exclude_init=False)
                        )
                        for local_module_path in proc.LOCAL_MODULES
                    ]
                )
            ))
        code = local_client.saveObject(object=code)
    else:
        code = None

    job_objects = []
    for args in argslist:
        _force_run = args.get('_force_run', None)
        _keep_temp_files = args.get('_keep_temp_files', None)
        _container = args.get('_container', None)
        _label = args.get('_label', None)
        _compute_requirements = args.get('_compute_requirements', None)
        _use_cache = args.get('_use_cache', True)
        _skip_failing = args.get('_skip_failing', None)
        _skip_timed_out = args.get('_skip_timed_out', None)
        _timeout = args.get('_timeout', None)
        _additional_files_to_realize = args.get('_additional_files_to_realize', None)

        if _force_run is None:
            _force_run = (os.environ.get('MLPROCESSORS_FORCE_RUN', '') == 'TRUE')

        if _skip_failing is None:
            _skip_failing = (os.environ.get('MLPROCESSORS_SKIP_FAILING', '') == 'TRUE')

        if _skip_timed_out is None:
            _skip_timed_out = (os.environ.get('MLPROCESSORS_SKIP_TIMED_OUT', '') == 'TRUE')

        if _keep_temp_files is None:
            _keep_temp_files = (os.environ.get('MLPROCESSORS_KEEP_TEMP_FILES', '') == 'TRUE')

        if _container == 'default':
            if hasattr(proc, 'CONTAINER'):
                _container = proc.CONTAINER

        if _container:
            if not _file_exists_or_is_sha1_url(_container):
                raise Exception('Unable to find container file: ' + _container)

        if _label is None:
            _label = '{} (version: {})'.format(proc.NAME, proc.VERSION)

        if _compute_requirements is None:
            _compute_requirements = dict()

        # hashes for inputs are computed below
        inputs = dict()
        for input0 in proc.INPUTS:
            name0 = input0.name
            if name0 in args:
                fname0 = args[name0]
                if input0.directory:
                    inputs[name0] = dict(
                        directory=True,
                        path=fname0
                    )
                else:
                    if not fname0:
                        inputs[name0] = None
                    if type(fname0) == str:
                        inputs[name0] = dict(
                            path=fname0
                        )
                    elif type(fname0) == list:
                        inputs[name0] = []
                        for a in fname0:
                            if type(a) == str:
                                inputs[name0].append(dict(
                                    path=a
                                ))
                            elif (type(a) == dict) and ('hash' in a):
                                inputs[name0].append(dict(
                                    path=None,
                                    object=a,
                                    hash=a['hash']
                                ))
                            elif hasattr(a, 'hash'):
                                if callable(a.hash):
                                    hash0 = a.hash()
                                else:
                                    hash0 = a.hash
                                inputs[name0].append(dict(
                                    path=None,
                                    object=a,
                                    hash=hash0
                                ))
                            elif a.get('pending', False):
                                inputs[name0].append(dict(
                                    object=a,
                                    pending=True
                                ))
                            else:
                                raise Exception('Input {} is a list and one of the members is not a string and is not pending.'.format(name0))
                    else:
                        if (type(fname0) == dict) and ('hash' in fname0):
                            inputs[name0] = dict(
                                path=None,
                                object=fname0,
                                hash=fname0['hash']
                            )
                        elif hasattr(fname0, 'hash'):
                            if callable(fname0.hash):
                                hash0 = fname0.hash()
                            else:
                                hash0 = fname0.hash
                            inputs[name0] = dict(
                                path=None,
                                object=fname0,
                                hash=hash0
                            )
                        elif fname0.get('pending', False):
                            inputs[name0] = dict(
                                object=fname0,
                                pending=True
                            )
                        else:
                            print(fname0)
                            raise Exception('Input {} is not a string and is not pending.'.format(name0))
            else:
                if not input0.optional:
                    raise Exception('Missing required input: {}'.format(name0))

        outputs = dict()
        for output0 in proc.OUTPUTS:
            name0 = output0.name
            if name0 in args:
                val0 = args[name0]
                if type(val0) == str:
                    _, file_extension = os.path.splitext(val0)
                    outputs[name0] = dict(
                        ext=file_extension,
                        dest_path=os.path.abspath(val0)
                    )
                elif type(val0) == dict:
                    outputs[name0] = val0
                elif type(val0) == bool:
                    if output0.is_array:
                        outputs[name0] = dict(ext='.npy')
                    elif output0.is_dict:
                        outputs[name0] = dict(ext='.json')
                    else:
                        outputs[name0] = dict(ext='.dat')
                else:
                    raise Exception('Type of output {} cannot be {}'.format(name0, str(type(val0))))
                if output0.is_array:
                    outputs[name0]['is_array'] = True
                if output0.is_array:
                    outputs[name0]['is_dict'] = True
            else:
                if not output0.optional:
                    raise Exception('Missing required output: {}'.format(name0))

        parameters = dict()
        parameters_to_hash = dict()
        for param0 in proc.PARAMETERS:
            name0 = param0.name
            if name0 not in args:
                if param0.optional:
                    val0 = param0.default
                else:
                    raise Exception('Missing required parameter: {}'.format(name0))
            else:
                val0 = args[name0]
            parameters[name0] = val0
            if not param0.environment:
                parameters_to_hash[name0] = val0

        if hasattr(proc, 'ENVIRONMENT_VARIABLES'):
            environment_variables = proc.ENVIRONMENT_VARIABLES
        else:
            environment_variables = []

        job_object = dict(
            processor_name=proc.NAME,
            processor_version=proc.VERSION,
            processor_class_name=proc.__name__,
            processor_code=code,
            label=_label,
            inputs=inputs,  # hashes are computed below
            outputs=outputs,
            parameters=parameters,
            parameters_to_hash=parameters_to_hash,
            container=_container,
            compute_requirements=_compute_requirements,
            force_run=_force_run,
            use_cache=_use_cache,
            skip_failing=_skip_failing,
            skip_timed_out=_skip_timed_out,
            keep_temp_files=_keep_temp_files,
            environment_variables=environment_variables,
            additional_files_to_realize=_additional_files_to_realize or [],
            timeout=_timeout
        )
        job_objects.append(job_object)

    all_kbucket_dir_inputs = []
    all_local_dir_inputs = []
    all_kbucket_file_inputs = []
    all_sha1_file_inputs = []
    all_placeholder_inputs = []
    all_placeholder_dir_inputs = []
    all_local_file_inputs = []
    for job_object in job_objects:
        for input_name, input0 in job_object['inputs'].items():
            if type(input0) == dict:
                path0 = input0.get('path', None)
                if path0:
                    if input0.get('directory', False):
                        if path0.startswith('kbucket://') or path0.startswith('sha1dir://'):
                            all_kbucket_dir_inputs.append(input0)
                        elif path0 == '<placeholder>':
                            all_placeholder_dir_inputs.append(input0)
                        else:
                            all_local_dir_inputs.append(input0)
                    else:
                        if path0.startswith('kbucket://') or path0.startswith('sha1dir://'):
                            all_kbucket_file_inputs.append(input0)
                        elif path0.startswith('sha1://'):
                            all_sha1_file_inputs.append(input0)
                        elif path0 == '<placeholder>':
                            all_placeholder_inputs.append(input0)
                        else:
                            all_local_file_inputs.append(input0)
            elif type(input0) == list:
                for a in input0:
                    path0 = a.get('path', None)
                    if path0:
                        if a.get('directory', False):
                            if path0.startswith('kbucket://') or path0.startswith('sha1dir://'):
                                all_kbucket_dir_inputs.append(a)
                            else:
                                all_local_dir_inputs.append(a)
                        else:
                            if path0.startswith('kbucket://') or path0.startswith('sha1dir://'):
                                all_kbucket_file_inputs.append(a)
                            elif path0.startswith('sha1://'):
                                all_sha1_file_inputs.append(a)
                            else:
                                all_local_file_inputs.append(a)
            else:
                raise Exception('Unexpected type for input {}'.format(input_name))

    # Prepare the local file inputs
    if len(all_local_file_inputs) > 0:
        mtlogging.sublog('Preparing local file inputs')
        if verbose:
            print('Preparing {} local file inputs'.format(len(all_local_file_inputs)))
        sha1s = _compute_sha1s_for_local_file_inputs(all_local_file_inputs)
        for ii in range(len(all_local_file_inputs)):
            all_local_file_inputs[ii]['sha1'] = sha1s[ii]

    # Prepare the kbucket file inputs
    if len(all_kbucket_file_inputs) > 0:
        mtlogging.sublog('Preparing kbucket file inputs')
        if verbose:
            print('Preparing {} kbucket file inputs'.format(len(all_kbucket_file_inputs)))
        sha1s = _compute_sha1s_for_kbucket_file_inputs(all_kbucket_file_inputs)
        for ii in range(len(all_kbucket_file_inputs)):
            all_kbucket_file_inputs[ii]['sha1'] = sha1s[ii]

    # Prepare the sha1 file inputs
    if len(all_sha1_file_inputs) > 0:
        mtlogging.sublog('Preparing sha1 file inputs')
        if verbose:
            print('Preparing {} sha1 file inputs'.format(len(all_sha1_file_inputs)))
        sha1s = _compute_sha1s_for_sha1_file_inputs(all_sha1_file_inputs)
        for ii in range(len(all_sha1_file_inputs)):
            all_sha1_file_inputs[ii]['sha1'] = sha1s[ii]

    # Prepare the local directory inputs
    if len(all_local_dir_inputs) > 0:
        mtlogging.sublog('Preparing local directory inputs')
        if verbose:
            print('Preparing {} local directory inputs'.format(len(all_local_dir_inputs)))
        hashes = _compute_hashes_for_local_dir_inputs(all_local_dir_inputs)
        for ii in range(len(all_local_dir_inputs)):
            all_local_dir_inputs[ii]['hash'] = hashes[ii]

    # Prepare the kbucket directory inputs
    if len(all_kbucket_dir_inputs) > 0:
        mtlogging.sublog('Preparing kbucket directory inputs')
        if verbose:
            print('Preparing {} kbucket directory inputs'.format(len(all_kbucket_dir_inputs)))
        hashes = _compute_hashes_for_kbucket_dir_inputs(all_kbucket_dir_inputs)
        for ii in range(len(all_kbucket_dir_inputs)):
            all_kbucket_dir_inputs[ii]['hash'] = hashes[ii]

    if verbose:
        print('.')

    return [MountainJob(processor=proc, job_object=job_object) for job_object in job_objects]


@mtlogging.log()
def createJob(
    proc,
    _container: Optional[str]=None,
    _use_cache: bool=True,
    _skip_failing: Optional[bool]=None,
    _skip_timed_out: Optional[bool]=None,
    _force_run: Optional[bool]=None,
    _keep_temp_files: Optional[bool]=None,
    _label: Optional[str]=None,
    _timeout: Optional[float]=None,
    _additional_files_to_realize: Optional[List[str]]=None,
    _verbose: Optional[bool]=None,
    **kwargs
) -> MountainJob:
    args = dict(
        _container=_container,
        _use_cache=_use_cache,
        _skip_failing=_skip_failing,
        _skip_timed_out=_skip_timed_out,
        _force_run=_force_run,
        _keep_temp_files=_keep_temp_files,
        _label=_label,
        _timeout=_timeout,
        _additional_files_to_realize=_additional_files_to_realize,
        **kwargs
    )
    jobs = createJobs(proc, [args], verbose=_verbose)
    return jobs[0]


def _read_python_code_of_directory(dirname, exclude_init, additional_files=[]):
    patterns = ['*.py'] + additional_files
    files = []
    dirs = []
    for fname in os.listdir(dirname):
        if os.path.isfile(dirname + '/' + fname):
            matches = False
            for pattern in patterns:
                if fnmatch.fnmatch(fname, pattern):
                    matches = True
            if exclude_init and (fname == '__init__.py'):
                matches = False
            if matches:
                with open(dirname + '/' + fname) as f:
                    txt = f.read()
                files.append(dict(
                    name=fname,
                    content=txt
                ))
        elif os.path.isdir(dirname + '/' + fname):
            if (not fname.startswith('__')) and (not fname.startswith('.')):
                content = _read_python_code_of_directory(
                    dirname + '/' + fname, additional_files=additional_files, exclude_init=False)
                if len(content['files']) + len(content['dirs']) > 0:
                    dirs.append(dict(
                        name=fname,
                        content=content
                    ))
    return dict(
        files=files,
        dirs=dirs
    )


def _file_exists_or_is_sha1_url(fname):
    if fname.startswith('sha1://'):
        return True
    if local_client.findFile(path=fname):
        return True
    return False


@mtlogging.log()
def _compute_sha1s_for_local_file_inputs(inputs):
    # do not parallelize if small number
    if len(inputs) <= 4:
        return [_compute_sha1_for_local_file_input(input0) for input0 in inputs]
    pool = multiprocessing.Pool(10)
    ret = pool.map(_compute_sha1_for_local_file_input, inputs)
    pool.close()
    pool.join()
    return ret


def _compute_sha1_for_local_file_input(input0):
    path0 = input0['path']
    if not os.path.exists(path0):
        raise Exception('Input file does not exists: {}'.format(path0))
    sha1 = local_client.computeFileSha1(path0)
    return sha1


@mtlogging.log()
def _compute_sha1s_for_kbucket_file_inputs(inputs):
    # do not parallelize if small number
    if len(inputs) <= 4:
        return [_compute_sha1_for_kbucket_file_input(input0) for input0 in inputs]
    pool = multiprocessing.Pool(10)
    ret = pool.map(_compute_sha1_for_kbucket_file_input, inputs)
    pool.close()
    pool.join()
    return ret


def _compute_sha1_for_kbucket_file_input(input0):
    path0 = input0['path']
    sha1 = local_client.computeFileSha1(path0)
    if not sha1:
        raise Exception('Unable to find input: {}'.format(path0))
    return sha1


@mtlogging.log()
def _compute_sha1s_for_sha1_file_inputs(inputs):
    # no need to parallelize -- fast enough
    ret = []
    for input0 in inputs:
        path0 = input0['path']
        sha1 = local_client.computeFileSha1(path0)
        if not sha1:
            raise Exception('Unable to find input: {}'.format(path0))
        ret.append(sha1)
    return ret


@mtlogging.log()
def _compute_hashes_for_local_dir_inputs(inputs):
    # do not parallelize if small number
    if len(inputs) <= 4:
        return [_compute_hash_for_local_dir_input(input0) for input0 in inputs]
    pool = multiprocessing.Pool(10)
    ret = pool.map(_compute_hash_for_local_dir_input, inputs)
    pool.close()
    pool.join()
    return ret


def _compute_hash_for_local_dir_input(input0):
    path0 = input0['path']
    if not os.path.isdir(path0):
        raise Exception('Input directory not found: {}'.format(path0))
    hash0 = local_client.computeDirHash(path0)
    if not hash0:
        raise Exception('Unable to compute hash of directory: {}'.format(path0))
    return hash0


@mtlogging.log()
def _compute_hashes_for_kbucket_dir_inputs(inputs):
    # do not parallelize if small number
    if len(inputs) <= 4:
        return [_compute_hash_for_kbucket_dir_input(input0) for input0 in inputs]
    pool = multiprocessing.Pool(10)
    ret = pool.map(_compute_hash_for_kbucket_dir_input, inputs)
    pool.close()
    pool.join()
    return ret


def _compute_hash_for_kbucket_dir_input(input0):
    path0 = input0['path']
    hash0 = local_client.computeDirHash(path0)
    if not hash0:
        raise Exception('Unable to compute hash of kbucket directory: {}'.format(path0))
    return hash0
