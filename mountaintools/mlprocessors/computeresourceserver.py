from mountaintools import CairioClient
import time
from .internal_run_batch_job import run_batch_job
import multiprocessing
import traceback
from .execute import _realize_required_files_for_jobs

class ComputeResourceServer():
    def __init__(self, *, resource_name=None, collection='', share_id='', token=None, upload_token=None):
        self._resource_name=resource_name
        self._cairio_client=CairioClient()
        self._local_client=CairioClient()
        self._collection=collection
        self._share_id=share_id
        if collection:
            self._cairio_client.configRemoteReadWrite(collection=collection,share_id=share_id,token=token,upload_token=upload_token)
        else:
            self._cairio_client.configLocal()
        self._last_console_message=''
        self._next_delay=0.25
        self._num_parallel=1
        self._srun_opts_string=''
    def mountainClient(self):
        return self._cairio_client
    def setNumParallel(self,num):
        self._num_parallel=num
    def setSrunOptsString(self,optstr):
        self._srun_opts_string=optstr
    def start(self):
        statuses_key=dict(
            name='compute_resource_batch_statuses',
            resource_name=self._resource_name
        )
        batch_statuses=self._cairio_client.getValue(key=statuses_key,subkey='-',parse_json=True)
        if batch_statuses is not None:
            for batch_id,status in batch_statuses.items():
                if (status!='finished') and (status!='pending') and (not status.startswith('error')):
                    print('Stopping batch {} with status {}'.format(batch_id,status))
                    self._cairio_client.setValue(key=statuses_key,subkey=batch_id,value='error: stopped because compute resource was restarted.')
        self._set_console_message('Starting compute resource: {}'.format(self._resource_name))
        self._next_delay=0.25
        while True:
            batch_statuses=self._cairio_client.getValue(key=statuses_key,subkey='-',parse_json=True)
            if (batch_statuses is None):
                self._set_console_message('Unable to read batch statuses.')
            else:
                pending_batch_ids=[]
                for batch_id,status in batch_statuses.items():
                    if status=='pending':
                        pending_batch_ids.append(batch_id)
                pending_batch_ids.sort()
                if len(pending_batch_ids)>0:
                    self._handle_batch(pending_batch_ids[0])
                    self._next_delay=0.25
                else:
                    self._set_console_message('No batches pending.')
            time.sleep(self._next_delay)
            self._next_delay=self._next_delay+0.25
            if self._next_delay>3:
                self._next_delay=3

    def _handle_batch(self,batch_id):
        self._set_console_message('Starting batch: {}'.format(batch_id))
        self._set_batch_status(batch_id=batch_id,status='starting')
        key=dict(
            name='compute_resource_batch_statuses',
            resource_name=self._resource_name
        )
        try:
            self._prepare_batch(batch_id)
        except:
            traceback.print_exc()
            print('Error preparing batch.')
            self._set_batch_status(batch_id=batch_id, status='error: Error preparing batch.')
            return

        monitor_job_statuses_process = multiprocessing.Process(target=_monitor_job_statuses, args=(batch_id, self._local_client, self._cairio_client))
        monitor_job_statuses_process.start()

        try:
            self._run_batch(batch_id)
        except:
            traceback.print_exc()
            print('Error running batch.')
            self._set_batch_status(batch_id=batch_id, status='error: Error running batch.')
            monitor_job_statuses_process.terminate()
            monitor_job_statuses_process.join()
            return

        monitor_job_statuses_process.terminate()
        monitor_job_statuses_process.join()

        

        try:
            self._assemble_batch(batch_id)
        except:
            traceback.print_exc()
            print('Error assembling batch.')
            self._set_batch_status(batch_id=batch_id, status='error: Error assembling batch')
            return

        self._check_batch_halt(batch_id)
        self._set_batch_status(batch_id=batch_id,status='finished')

    def _check_batch_halt(self,batch_id):
        key=dict(
            name='compute_resource_batch_halt',
            batch_id=batch_id
        )
        val=self._cairio_client.getValue(key=key)
        if val is not None:
            print('BATCH HALTED (batch_id={})'.format(batch_id))
            # also save it locally so we can potentially stop the individual jobs
            self._local_client.setValue(key=key,value=val)
            raise Exception('Stopping batch (batch_id={})'.format(batch_id))
            
    def _set_batch_status(self,*,batch_id,status):
        key=dict(
            name='compute_resource_batch_statuses',
            resource_name=self._resource_name
        )
        self._cairio_client.setValue(key=key,subkey=batch_id,value=status)

    def _prepare_batch(self,batch_id):
        self._check_batch_halt(batch_id)
        self._set_batch_status(batch_id=batch_id,status='preparing')
        self._set_console_message('Preparing batch: {}'.format(batch_id))
        # first we download the batch to the local database so we can use the local_client
        key_batch=dict(
            name='compute_resource_batch',
            batch_id=batch_id
        )
        batch=self._cairio_client.loadObject(
            key=key_batch    
        )
        self._local_client.saveObject(
            key=key_batch,
            object=batch
        )
        jobs=batch['jobs']
        _realize_required_files_for_jobs(cairio_client=self._cairio_client, jobs=jobs, realize_code=True)
    
    def _run_batch(self,batch_id):
        self._check_batch_halt(batch_id)
        self._set_batch_status(batch_id=batch_id,status='running')
        self._set_console_message('Running batch: {}'.format(batch_id))
        # in the prepare step, we have it locally
        batch=self._local_client.loadObject(
            key=dict(
                name='compute_resource_batch',
                batch_id=batch_id
            )
        )
        jobs=batch['jobs']

        system_call=True
        run_batch_job_args=[
            dict(
                collection=self._collection,
                share_id=self._share_id,
                batch_id=batch_id,
                job_index=ii,
                system_call=system_call,
                srun_opts_string=None
            )
            for ii in range(len(jobs))
        ]
        if self._num_parallel>1:
            if self._srun_opts_string:
                raise Exception('Cannot use parallel>1 with srun.')
            print('Running in parallel (num_parallel={}).'.format(self._num_parallel))
            pool = multiprocessing.Pool(self._num_parallel)
            pool.map(_run_batch_job_helper, run_batch_job_args)
            pool.close()
            pool.join()
        elif self._srun_opts_string:
            if len(run_batch_job_args)>0:
                bjargs=run_batch_job_args[0].copy()
                bjargs['job_index']=None
                bjargs['srun_opts_string']=self._srun_opts_string
                run_batch_job(**bjargs)
        else:
            for ii in range(len(jobs)):
                run_batch_job(**run_batch_job_args[ii])
                self._check_batch_halt(batch_id)
        

    def _assemble_batch(self,batch_id):
        self._check_batch_halt(batch_id)
        self._set_batch_status(batch_id=batch_id,status='assembling')
        self._set_console_message('Assembling batch: {}'.format(batch_id))
        # from the prepare step, we have it locally
        batch=self._local_client.loadObject(
            key=dict(
                name='compute_resource_batch',
                batch_id=batch_id
            )
        )
        jobs=batch['jobs']

        self._set_batch_status(batch_id=batch_id,status='assembling: {} jobs'.format(len(jobs)))

        pool=multiprocessing.Pool(20)
        results=pool.map(_assemble_job_result,[
            dict(
                local_client=self._local_client,
                cairio_client=self._cairio_client,
                batch_id=batch_id,
                job=jobs[job_index],
                job_index=job_index
            )
            for job_index in range(len(jobs))
        ])
        pool.close()
        pool.join()

        # keys=[
        #     dict(
        #         name='compute_resource_batch_job_result',batch_id=batch_id,job_index=ii
        #     )
        #     for ii in range(len(jobs))
        # ]
        # # we can load the results from local database
        # results0=_load_objects(self._local_client,keys=keys)
        # results = []
        # for ii, job in enumerate(jobs):
        #     result0=results0[ii]
        #     result=dict(
        #         job=job,
        #         result=result0
        #     )
        #     results.append(result)

        #     output_signatures=result0.get('output_signatures',dict())
        #     for name0, signature0 in output_signatures.items():
        #         sha1=self._local_client.getValue(key=signature0)
        #         # propagate to remote database
        #         self._cairio_client.setValue(key=signature0, value=sha1)

        #     result_outputs0=result0['outputs']
        #     for name0, output0 in job['outputs'].items():
        #         if name0 not in result_outputs0:
        #             raise Exception('Unexpected: output {} not found in result'.format(name0))
        #         result_output0=result_outputs0[name0]
        #         if type(output0)==dict:    
        #             if output0.get('upload', False):
        #                 print('Saving output {}...'.format(name0))
        #                 self._cairio_client.saveFile(path=result_output0)

        #     if ('console_out' in result0) and result0['console_out']:
        #         self._cairio_client.saveFile(path=result0['console_out'])

        # results = []
        # for ii, job in enumerate(jobs):
        #     print('Assembling job {} of {}'.format(ii,len(jobs)))
        #     self._set_batch_status(batch_id=batch_id,status='assembling: job {} of {}'.format(ii,len(jobs)))
        #     self._check_batch_halt(batch_id)
        #     result0=self._local_client.loadObject(key=dict(name='compute_resource_batch_job_result',batch_id=batch_id,job_index=ii))
        #     result=dict(
        #         job=job,
        #         result=result0
        #     )
        #     results.append(result)

        self._check_batch_halt(batch_id)
        
        results_key=dict(
            name='compute_resource_batch_results',
            batch_id=batch_id
        )
        print('Saving results...', results_key)

        # finally, save the results remotely
        self._cairio_client.saveObject(
            key=results_key,
            object=dict(
                results=results
            )
        )

        print('Done.')

        self._check_batch_halt(batch_id)
    
    def _set_console_message(self,msg):
        if msg == self._last_console_message:
            return
        print('{}: {}'.format(self._resource_name,msg))
        self._last_console_message=msg

def _monitor_job_statuses(batch_id, local_client, remote_client):
    key=dict(
        name='compute_resource_batch_job_statuses',
        batch_id=batch_id
    )
    last_obj=dict()
    while True:
        obj=local_client.getValue(key=key,subkey='-',parse_json=True)
        if obj is not None:
            for job_index,status in obj.items():
                if obj[job_index]!=last_obj.get(job_index,None):
                    remote_client.setValue(key=key,subkey=job_index,value=status)
            last_obj=obj
        time.sleep(2)

def _run_batch_job_helper(kwargs):
    run_batch_job(**kwargs)

def _load_objects(cairio_client,keys):
    pool = multiprocessing.Pool(20)
    objects=pool.map(_load_objects_helper, [(cairio_client,key) for key in keys])
    pool.close()
    pool.join()
    for ii,object in enumerate(objects):
        if object is None:
            print('Loading missed object...')
            objects[ii]=cairio_client.loadObject(key=keys[ii])
            if objects[ii] is None:
                raise Exception('Unable to load object for key:',keys[ii])
    return objects

    # ret=[]
    # for key in keys:
    #     ret.append(cairio_client.loadObject(key=key))
    # return ret

def _load_objects_helper(args):
    cairio_client=args[0]
    key=args[1]
    return cairio_client.loadObject(key=key)

def _assemble_job_result(kwargs):
    local_client=kwargs['local_client']
    cairio_client=kwargs['cairio_client']
    batch_id=kwargs['batch_id']
    job=kwargs['job']
    job_index=kwargs['job_index']
    key=dict(
            name='compute_resource_batch_job_result',batch_id=batch_id,job_index=job_index
        )
    # we can load the results from local database
    result0=local_client.loadObject(key=key)
    result=dict(
        job=job,
        result=result0
    )

    output_signatures=result0.get('output_signatures',dict())
    if output_signatures:
        for name0, signature0 in output_signatures.items():
            sha1=local_client.getValue(key=signature0)
            # propagate to remote database
            cairio_client.setValue(key=signature0, value=sha1)

    result_outputs0=result0.get('outputs', None)
    if result_outputs0:
        for name0, output0 in job['outputs'].items():
            if name0 not in result_outputs0:
                raise Exception('Unexpected: output {} not found in result'.format(name0))
            result_output0=result_outputs0[name0]
            if type(output0)==dict:    
                if output0.get('upload', False):
                    print('Saving output {}...'.format(name0))
                    cairio_client.saveFile(path=result_output0)

    if ('console_out' in result0) and result0['console_out']:
        cairio_client.saveFile(path=result0['console_out'])
    
    return result