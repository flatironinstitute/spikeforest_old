import time
import multiprocessing
import traceback
from .mountainjob import MountainJob
from .executebatch import executeBatch
from mountaintools import client as mt
import mtlogging

class ComputeResourceServer():
    def __init__(self, *, resource_name=None, collection=None, kachery_name=None):
        self._resource_name=resource_name
        self._collection=collection
        self._kachery_name=kachery_name
        self._last_console_message=''
        self._next_delay=0.25
        self._num_parallel=None
        self._srun_opts_string=''

    # def mountainClient(self):
    #     return self._cairio_client

    def setNumParallel(self,num):
        self._num_parallel=num

    def setSrunOptsString(self,optstr):
        self._srun_opts_string=optstr

    @mtlogging.log(name='ComputeResourceServer:start')
    def start(self, exit_event=None):
        print('registering compute resource: ', self._resource_name)
        mt.setValue(
            key=dict(name='compute_resources'),
            subkey=self._resource_name,
            value='exists',
            collection=self._collection
        ) # remote
        statuses_key=dict(
            name='compute_resource_batch_statuses',
            resource_name=self._resource_name
        )
        batch_statuses=mt.getValue(key=statuses_key,subkey='-',parse_json=True,collection=self._collection) # remote
        if batch_statuses is not None:
            for batch_id,status in batch_statuses.items():
                if (status!='finished') and (status!='pending') and (not status.startswith('error')):
                    print('Stopping batch {} with status {}'.format(batch_id,status))
                    mt.setValue(key=statuses_key,subkey=batch_id,value='error: stopped because compute resource was restarted.',collection=self._collection) # remote
        self._set_console_message('Starting compute resource: {}'.format(self._resource_name))
        self._next_delay=0.25
        while True:
            if exit_event and exit_event.is_set():
                print('Exiting compute resource...')
                return
            batch_statuses=mt.getValue(key=statuses_key,subkey='-',parse_json=True,collection=self._collection) # remote
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

    @mtlogging.log()
    def _handle_batch(self,batch_id):
        self._set_console_message('Starting batch: {}'.format(batch_id))
        self._set_batch_status(batch_id=batch_id,status='starting')

        # get the batch and save it locally
        key = dict(
            name='compute_resource_batch',
            batch_id=batch_id
        )
        batch = mt.loadObject(key = key, collection=self._collection, download_from=self._kachery_name) # remote
        if not batch:
            raise Exception('Unable to load batch object.')
        mt.saveObject(key = key, object=batch) # local

        try:
            self._run_batch(batch_id)
        except:
            traceback.print_exc()
            print('Error running batch.')
            self._set_batch_status(batch_id=batch_id, status='error')
            return

        self._set_batch_status(batch_id=batch_id,status='finalizing-job-statuses') # this should trigger the monitor to end

        job_status_key = _get_job_status_key(batch_id) 
        status_obj = mt.getValue(key=job_status_key,subkey='-',parse_json=True) # local
        if status_obj is not None:
            for job_index, status in status_obj.items():
                mt.setValue(key=job_status_key, subkey=str(job_index), value=status, collection=self._collection) # remote

        self._check_batch_halt(batch_id)
        self._set_batch_status(batch_id=batch_id,status='finished')

    @mtlogging.log()
    def _check_batch_halt(self,batch_id):
        halt_key=_get_halt_key(batch_id)
        val=mt.getValue(key=halt_key, collection=self._collection) # remote
        if val is not None:
            print('BATCH HALTED (batch_id={})'.format(batch_id))
            # also save it locally so we can potentially stop the individual jobs
            mt.setValue(key=halt_key,value=val) # local
            raise Exception('Stopping batch (batch_id={})'.format(batch_id))

    @mtlogging.log()
    def _set_batch_status(self,*,batch_id,status):
        key=dict(
            name='compute_resource_batch_statuses',
            resource_name=self._resource_name
        )
        mt.setValue(key=key,subkey=batch_id,value=status) # local
        mt.setValue(key=key,subkey=batch_id,value=status,collection=self._collection) # remote
    
    @mtlogging.log()
    def _get_batch_status(self,*,batch_id):
        key=dict(
            name='compute_resource_batch_statuses',
            resource_name=self._resource_name
        )
        return mt.getValue(key=key,subkey=batch_id) # local
    
    @mtlogging.log()
    def _run_batch(self, batch_id):
        self._check_batch_halt(batch_id)
        self._set_batch_status(batch_id=batch_id,status='loading')
        self._set_console_message('Loading batch: {}'.format(batch_id))
        
        key = dict(
            name='compute_resource_batch',
            batch_id=batch_id
        )
        batch = mt.loadObject(key = key) # local
        if not batch:
            raise Exception('Unable to load batch object locally for batch id: {}'.format(batch_id))

        batch_status_key = dict(
            name='compute_resource_batch_statuses',
            resource_name=self._resource_name
        )
        
        job_objects = batch['jobs']
        jobs = []
        for job_object in job_objects:
            job = MountainJob(job_object=job_object)
            jobs.append(job)
        
        self._check_batch_halt(batch_id)
        self._set_batch_status(batch_id=batch_id,status='running')
        self._set_console_message('Starting batch: {}'.format(batch_id))

        # Start the job monitor (it will end when the batch status is no longer running)
        monitor_job_statuses_process = multiprocessing.Process(target=_monitor_job_statuses, args=(batch_id, self._collection, self._kachery_name, batch_status_key))
        monitor_job_statuses_process.start()

        results = executeBatch(jobs=jobs, label=batch.get('label', batch_id), num_workers=self._num_parallel, compute_resource=None, halt_key=_get_halt_key(batch_id), job_status_key=_get_job_status_key(batch_id), job_result_key=_get_job_result_key(batch_id), srun_opts=self._srun_opts_string)

        self._check_batch_halt(batch_id)
        self._set_batch_status(batch_id=batch_id,status='saving-outputs')
        self._set_console_message('Saving/uploading outputs: {}'.format(batch_id))

        pool = multiprocessing.Pool(20)
        result_objects = pool.map(_save_results_helper, [dict(result=result, collection=self._collection, kachery_name=self._kachery_name, label='result {} of {}'.format(ii, len(results))) for ii, result in enumerate(results)])
        pool.close()
        pool.join()
        
        self._set_batch_status(batch_id=batch_id,status='saving-results')
        self._set_console_message('Saving/uploading results: {}'.format(batch_id))
        mt.saveObject(
            key = dict(
                name='compute_resource_batch_results',
                batch_id=batch_id
            ),
            object=dict(
                results = result_objects
            ),
            collection=self._collection,
            upload_to=self._kachery_name
        ) # remote

        # if it hasn't already stopped
        monitor_job_statuses_process.terminate()
    
    @mtlogging.log()
    def _set_console_message(self,msg):
        if msg == self._last_console_message:
            return
        print('{}: {}'.format(self._resource_name, msg))
        self._last_console_message=msg

def _save_results_helper(kwargs):
    return _save_results(**kwargs)

def _save_results(result, collection, kachery_name, label):
    if result is None:
        return None
    if (result.retcode==0) and (result.outputs):
        for output_name, output_fname in result.outputs.items():
            print('Saving/uploading {} for {}: {}...'.format(output_name, label, output_fname))
            a = mt.saveFile(path=output_fname, upload_to=kachery_name) # remote
            if not a:
                print('Warning: Unable to save/upload file: {}'.format(output_fname))
    if result.console_out:
        print('Saving/uploading console output...')
        mt.saveFile(path=result.console_out, upload_to=kachery_name) # remote
    result_object = dict(
        retcode = result.retcode,
        console_out = result.console_out,
        runtime_info = result.runtime_info,
        outputs = result.outputs
    )
    return result_object

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

def _monitor_job_statuses(batch_id, collection, kachery_name, batch_status_key):
    job_status_key=_get_job_status_key(batch_id) 
    job_result_key=_get_job_result_key(batch_id) 
    halt_key=_get_halt_key(batch_id)
    
    last_status_obj = dict()
    while True:
        batch_status = mt.getValue(key=batch_status_key,subkey=batch_id) # local
        if batch_status != 'running':
            print('Stopping job monitor because batch status is: '+batch_status)
            return
        status_obj = mt.getValue(key=job_status_key,subkey='-',parse_json=True) # local
        if status_obj is not None:
            job_indices_changed = []
            for job_index, status in status_obj.items():
                if status_obj[job_index] != last_status_obj.get(job_index,None):
                    job_indices_changed.append(job_index)
            for job_index in job_indices_changed:
                mt.setValue(key=job_status_key, subkey=str(job_index), value=status, collection=collection) # remote
            for job_index in job_indices_changed:
                result0 = mt.loadObject(key=job_result_key, subkey=str(job_index)) # local
                if result0:
                    print('Uploading result for job {}'.format(job_index))
                    mt.saveObject(key=job_result_key, subkey=str(job_index), object=result0, collection=collection, upload_to=kachery_name) # remote
                    if 'console_out' in result0:
                        mt.saveFile(path=result0['console_out'], upload_to=kachery_name) # remote
            last_status_obj = status_obj

        halt_val = mt.getValue(key=halt_key, collection=collection) # remote
        if halt_val is not None:
            print('BATCH HALTED (batch_id={})'.format(batch_id))
            # also save it locally so we can potentially stop the individual jobs
            mt.setValue(key=halt_key,value=halt_val) # local
            return # is this the best thing to do?

        # result_obj = local_client.getValue(key=job_result_key,subkey='-',parse_json=True)
        # if result_obj is not None:
        #     for job_index, resultval in result_obj.items():
        #         if result_obj[job_index] != last_result_obj.get(job_index,None):
        #             result0 = local_client.loadObject(key=job_result_key, subkey=str(job_index))
        #             if result0:
        #                 remote_client.saveObject(key=job_result_key, subkey=str(job_index), object=result0)
        #                 if 'console_out' in result0:
        #                     remote_client.saveFile(path=result0['console_out'])
        #     last_result_obj = result_obj
        time.sleep(2)