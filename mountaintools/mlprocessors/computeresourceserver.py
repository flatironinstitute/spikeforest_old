from cairio import CairioClient
import time
from mlprocessors import _prepare_processor_job
from .internal_run_batch_job import run_batch_job
import multiprocessing
import traceback

# global
_realized_files = set()

class ComputeResourceServer():
    def __init__(self, *, resource_name=None, collection='', share_id='', token=None, upload_token=None):
        self._resource_name=resource_name
        self._cairio_client=CairioClient()
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
                print('Clearing batch {} with status {}'.format(batch_id,status))
                self._cairio_client.setValue(key=statuses_key,subkey=batch_id,value=None)
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

        try:
            self._run_batch(batch_id)
        except:
            traceback.print_exc()
            print('Error running batch.')
            self._set_batch_status(batch_id=batch_id, status='error: Error running batch.')
            return

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
        batch=self._cairio_client.loadObject(
            key=dict(
                name='compute_resource_batch',
                batch_id=batch_id
            )
        )
        jobs=batch['jobs']
        containers_to_realize=set()
        files_to_realize=set()
        for ii,job in enumerate(jobs):
            container0 = job.get('container', None)
            if container0 is not None:
                containers_to_realize.add(container0)
            files_to_realize0 = job.get('files_to_realize', [])
            for f0 in files_to_realize0:
                files_to_realize.add(f0)
        if len(containers_to_realize)>0:
            print('Realizing {} containers...'.format(len(containers_to_realize)))
            self._realize_files(containers_to_realize)
        if len(files_to_realize)>0:
            print('Realizing {} files...'.format(len(files_to_realize)))
            self._realize_files(files_to_realize)

    def _realize_files(self,files):
        for file0 in files:
            if file0 not in _realized_files:
                a=self._cairio_client.realizeFile(file0)
                if a:
                    _realized_files.add(a)
                else:
                    raise Exception('Unable to realize file: '+file0)


    # def _prepare_processor_job(job):
    #     container = job.get('container', None)
    #     if container:
    #         if container not in _realized_containers:
    #             print('realizing container: '+container)
    #             a = ca.realizeFile(path=container)
    #             if a:
    #                 _realized_containers.add(container)
    #             else:
    #                 raise Exception('Unable to realize container file: '+container)
    #     files_to_realize = job.get('files_to_realize', [])
    #     for fname in files_to_realize:
    #         print('realizing file: '+fname)
    #         a = ca.realizeFile(path=fname)
    #         if not a:
    #             raise Exception('Unable to realize file: '+fname)
    
    def _run_batch(self,batch_id):
        self._check_batch_halt(batch_id)
        self._set_batch_status(batch_id=batch_id,status='running')
        self._set_console_message('Running batch: {}'.format(batch_id))
        batch=self._cairio_client.loadObject(
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
                token=self._cairio_client.getRemoteConfig()['token'],
                upload_token=self._cairio_client.getRemoteConfig()['upload_token'],
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
                self._set_batch_status(batch_id=batch_id,status='running: {} of {}'.format(ii, len(jobs)))
                run_batch_job(**run_batch_job_args[ii])
                self._check_batch_halt(batch_id)

    def _assemble_batch(self,batch_id):
        self._check_batch_halt(batch_id)
        self._set_batch_status(batch_id=batch_id,status='assembling')
        self._set_console_message('Assembling batch: {}'.format(batch_id))
        batch=self._cairio_client.loadObject(
            key=dict(
                name='compute_resource_batch',
                batch_id=batch_id
            )
        )
        jobs=batch['jobs']

        keys=[
            dict(
                name='compute_resource_batch_job_result',job_index=ii
            )
            for ii in range(len(jobs))
        ]
        results0=_load_objects(self._cairio_client,keys=keys)
        results = []
        for ii, job in enumerate(jobs):
            result0=results0[ii]
            result=dict(
                job=job,
                result=result0
            )
            results.append(result)

        # results = []
        # for ii, job in enumerate(jobs):
        #     print('Assembling job {} of {}'.format(ii,len(jobs)))
        #     self._set_batch_status(batch_id=batch_id,status='assembling: job {} of {}'.format(ii,len(jobs)))
        #     self._check_batch_halt(batch_id)
        #     result0=self._cairio_client.loadObject(key=dict(name='compute_resource_batch_job_result',job_index=ii))
        #     result=dict(
        #         job=job,
        #         result=result0
        #     )
        #     results.append(result)

        self._check_batch_halt(batch_id)
        
        self._cairio_client.saveObject(
            key=dict(
                name='compute_resource_batch_results',
                batch_id=batch_id
            ),
            object=dict(
                results=results
            )
        )

        self._check_batch_halt(batch_id)
    
    def _set_console_message(self,msg):
        if msg == self._last_console_message:
            return
        print('{}: {}'.format(self._resource_name,msg))
        self._last_console_message=msg


def _run_batch_job_helper(kwargs):
    run_batch_job(**kwargs)

def _load_objects(cairio_client,keys):
    pool = multiprocessing.Pool(20)
    objects=pool.map(_load_objects_helper, [(cairio_client,key) for key in keys])
    pool.close()
    pool.join()
    return objects

    # ret=[]
    # for key in keys:
    #     ret.append(cairio_client.loadObject(key=key))
    # return ret

def _load_objects_helper(args):
    cairio_client=args[0]
    key=args[1]
    return cairio_client.loadObject(key=key)

    