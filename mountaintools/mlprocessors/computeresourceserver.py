from mountaintools import CairioClient
import time
import multiprocessing
import traceback
from .mountainjob import MountainJob
from .executebatch import executeBatch
from .internal_run_batch_job import run_batch_job

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
        self._num_parallel=None
        self._srun_opts_string=''

    def mountainClient(self):
        return self._cairio_client

    def setNumParallel(self,num):
        self._num_parallel=num

    def setSrunOptsString(self,optstr):
        self._srun_opts_string=optstr

    def start(self):
        print('registering computer resource: ', self._resource_name)
        self._cairio_client.setValue(
            key=dict(name='compute_resources'),
            subkey=self._resource_name,
            value='exists'
        )
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

        monitor_job_statuses_process = multiprocessing.Process(target=_monitor_job_statuses, args=(batch_id, self._local_client, self._cairio_client))
        monitor_job_statuses_process.start()

        try:
            self._run_batch(batch_id)
        except:
            traceback.print_exc()
            print('Error running batch.')
            self._set_batch_status(batch_id=batch_id, status='error')
            monitor_job_statuses_process.terminate()
            monitor_job_statuses_process.join()
            return

        monitor_job_statuses_process.terminate()
        monitor_job_statuses_process.join()

        self._check_batch_halt(batch_id)
        self._set_batch_status(batch_id=batch_id,status='finished')

    def _check_batch_halt(self,batch_id):
        halt_key=_get_halt_key(batch_id)
        val=self._cairio_client.getValue(key=halt_key)
        if val is not None:
            print('BATCH HALTED (batch_id={})'.format(batch_id))
            # also save it locally so we can potentially stop the individual jobs
            self._local_client.setValue(key=halt_key,value=val)
            raise Exception('Stopping batch (batch_id={})'.format(batch_id))
            
    def _set_batch_status(self,*,batch_id,status):
        key=dict(
            name='compute_resource_batch_statuses',
            resource_name=self._resource_name
        )
        self._cairio_client.setValue(key=key,subkey=batch_id,value=status)
    
    def _run_batch(self, batch_id):
        self._check_batch_halt(batch_id)
        self._set_batch_status(batch_id=batch_id,status='loading')
        self._set_console_message('Loading batch: {}'.format(batch_id))
        
        key = dict(
            name='compute_resource_batch',
            batch_id=batch_id
        )
        batch = self._cairio_client.loadObject(key = key)

        # save it locally
        self._local_client.saveObject(key = key, object=batch)
        batch=self._local_client.loadObject(
            key=dict(
                name='compute_resource_batch',
                batch_id=batch_id
            )
        )
        
        job_objects = batch['jobs']
        jobs = []
        for job_object in job_objects:
            job = MountainJob()
            job.initFromObject(job_object)
            jobs.append(job)
        
        self._check_batch_halt(batch_id)
        self._set_batch_status(batch_id=batch_id,status='running')
        self._set_console_message('Starting batch: {}'.format(batch_id))
        results = executeBatch(jobs=jobs, label=batch.get('label', batch_id), num_workers=self._num_parallel, compute_resource=None, halt_key=_get_halt_key(batch_id), job_status_key=_get_job_status_key(batch_id), job_result_key=_get_job_result_key(batch_id), srun_opts=self._srun_opts_string)

        self._check_batch_halt(batch_id)
        self._set_batch_status(batch_id=batch_id,status='saving')
        self._set_console_message('Saving/uploading outputs: {}'.format(batch_id))

        result_objects = []
        # TODO: do the following in a multiprocessing pool
        for result in results:
            if (result.retcode==0) and (result.outputs):
                for output_name, output_fname in result.outputs.items():
                    self._set_console_message('Saving/uploading {}: {}...'.format(output_name, output_fname))
                    a = self._cairio_client.saveFile(path=output_fname)
                    if not a:
                        print('Warning: Unable to save/upload file: {}'.format(output_fname))
            if result.console_out:
                self._set_console_message('Saving/uploading console output...')
                self._cairio_client.saveFile(path=result.console_out)
            result_object = dict(
                retcode = result.retcode,
                console_out = result.console_out,
                runtime_info = result.runtime_info,
                outputs = result.outputs
            )
            result_objects.append(result_object)
        
        self._set_batch_status(batch_id=batch_id,status='saving')
        self._set_console_message('Saving/uploading results: {}'.format(batch_id))
        self._cairio_client.saveObject(
            key = dict(
                name='compute_resource_batch_results',
                batch_id=batch_id
            ),
            object=dict(
                results = result_objects
            )
        )
    
    def _set_console_message(self,msg):
        if msg == self._last_console_message:
            return
        print('{}: {}'.format(self._resource_name, msg))
        self._last_console_message=msg

def _get_job_status_key(batch_id):
    return dict(
        name='compute_resource_batch_job_statuses',
        batch_id=batch_id
    )

def _get_job_result_key(batch_id):
    return dict(
        name='compute_resource_batch_job_results',
        batch_id=batch_id
    )

def _get_halt_key(batch_id):
    return dict(
        name='compute_resource_batch_halt',
        batch_id=batch_id
    )

def _monitor_job_statuses(batch_id, local_client, remote_client):
    job_status_key=_get_job_status_key(batch_id) 
    job_result_key=_get_job_result_key(batch_id) 
    halt_key=_get_halt_key(batch_id)
    
    last_status_obj = dict()
    last_result_obj = dict()
    while True:
        status_obj = local_client.getValue(key=job_status_key,subkey='-',parse_json=True)
        if status_obj is not None:
            for job_index, status in status_obj.items():
                if status_obj[job_index] != last_status_obj.get(job_index,None):
                    remote_client.setValue(key=job_status_key, subkey=str(job_index), value=status)
            last_status_obj = status_obj

        halt_val = remote_client.getValue(key=halt_key)
        if halt_val is not None:
            print('BATCH HALTED (batch_id={})'.format(batch_id))
            # also save it locally so we can potentially stop the individual jobs
            local_client.setValue(key=halt_key,value=halt_val)
            return # is this the best thing to do?

        result_obj = local_client.getValue(key=job_result_key,subkey='-',parse_json=True)
        if result_obj is not None:
            for job_index, resultval in result_obj.items():
                if result_obj[job_index] != last_result_obj.get(job_index,None):
                    result0 = local_client.loadObject(key=job_result_key, subkey=str(job_index))
                    if result0:
                        remote_client.saveObject(key=job_result_key, subkey=str(job_index), object=result0)
                        if 'console_out' in result0:
                            remote_client.saveFile(path=result0['console_out'])
            last_result_obj = result_obj
        time.sleep(2)