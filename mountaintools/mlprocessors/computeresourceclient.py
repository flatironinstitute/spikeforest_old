from mountainclient import MountainClient
import time
import random
from .mountainjob import MountainJobResult
from .mountainjob import MountainJob

class ComputeResourceClient():
    def __init__(self, resource_name, collection='', share_id='', token=None, upload_token=None, readonly=False):
        self._resource_name=resource_name
        self._cairio_client=MountainClient()
        if collection:
            if readonly:
                self._cairio_client.configRemoteReadonly(collection=collection,share_id=share_id)
            else:
                self._cairio_client.configRemoteReadWrite(collection=collection,share_id=share_id,token=token,upload_token=upload_token)
        else:
            self._cairio_client.configLocal()
        self._last_console_message=''
        self._next_delay=0.25
    def initializeBatch(self,*,jobs, label='unlabeled'):
        batch_id = 'batch_{}_{}'.format(time.time()-0, _random_string(6))

        job_objects = []
        for job in jobs:
            job_objects.append(job.getObject())
        
        key=dict(
            name='compute_resource_batch',
            batch_id=batch_id
        )
        self._cairio_client.saveObject(
            key=key,
            object=dict(
                label=label,
                jobs=job_objects
            )
        )
        return batch_id
    def getBatch(self, *, batch_id):
        key=dict(
            name='compute_resource_batch',
            batch_id=batch_id
        )
        batch=self._cairio_client.loadObject(
            key=key
        )
        return batch
    
    def startBatch(self,*,batch_id):
        self._cairio_client.setValue(
            key=dict(
                name='compute_resource_batch_halt',
                batch_id=batch_id
            ),
            value=None
        )
        self._cairio_client.setValue(
            key=dict(
                name='compute_resource_batch_statuses',
                resource_name=self._resource_name
            ),
            subkey=batch_id,
            value='pending'
        )
    def stopBatch(self,*,batch_id):
        self._cairio_client.setValue(
            key=dict(
                name='compute_resource_batch_halt',
                batch_id=batch_id
            ),
            value='halt'
        )
    def monitorBatch(self,*,batch_id):
        self._next_delay=0.25
        while True:
            status0=self.getBatchStatus(batch_id=batch_id)
            if status0 is None:
                self._set_console_message('Unable to determine status.')
            elif status0=='pending':
                self._set_console_message('Waiting for batch to start.')
            elif status0=='finished':
                self._set_console_message('Batch is finished.')
                # self._finalize_batch(batch_id=batch_id)
                return
            elif status0=='running':
                statuses=self._get_batch_job_statuses(batch_id=batch_id)
                if statuses is None:
                    self._set_console_message('{} ---'.format(status0))
                else:
                    statuses_list = list(statuses.values())
                    num_running = statuses_list.count('running')
                    num_finished = statuses_list.count('finished')
                    num_errors = statuses_list.count('error')
                    update_string = '{}: {} running, {} finished, {} errors'.format(status0, num_running, num_finished, num_errors)
                    #update_string = '({})\n{} --- {}: {} ready, {} running, {} finished, {} total jobs'.format(
                    #    batch_name, label, batch_status0, num_ready, num_running, num_finished, len(jobs))
                    self._set_console_message(update_string)
            elif status0.startswith('error'):
                self._set_console_message('Error running batch: '+status0)
                return
            else:
                self._set_console_message(status0)
            time.sleep(self._next_delay)
            self._next_delay=self._next_delay+0.25
            if self._next_delay>3:
                self._next_delay=3
        
    def getBatchStatuses(self):
        batch_statuses = self._cairio_client.getValue(
            key=dict(
                name='compute_resource_batch_statuses',
                resource_name=self._resource_name,
            ),
            subkey='-',
            parse_json=True
        )
        return batch_statuses

    def getBatchJobStatuses(self, *, batch_id):
        return self._get_batch_job_statuses(batch_id=batch_id)

    def _get_batch_job_statuses(self,*,batch_id):
        return self._cairio_client.getValue(
            key=dict(
                name='compute_resource_batch_job_statuses',
                batch_id=batch_id
            ),
            subkey='-',
            parse_json=True
        )

    def getBatchStatus(self,*,batch_id):
        return self._cairio_client.getValue(
            key=dict(
                name='compute_resource_batch_statuses',
                resource_name=self._resource_name
            ),
            subkey=batch_id
        )

    def getBatchJobResults(self,*,batch_id):
        key=dict(
            name='compute_resource_batch_results',
            batch_id=batch_id
        )
        obj = self._cairio_client.loadObject(
            key=key
        )
        if obj is None:
            return None
        result_objects = obj['results']
        ret = []
        for result_object in result_objects:
            R = MountainJobResult()
            R.console_out = result_object['console_out']
            R.runtime_info = result_object['runtime_info']
            R.retcode = result_object['retcode']
            R.outputs = result_object['outputs']
            ret.append(R)
        return ret
    def _set_console_message(self,msg):
        if msg == self._last_console_message:
            return
        self._next_delay=0.25
        print('{}'.format(msg))
        self._last_console_message=msg

def _random_string(num_chars):
    chars = 'abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789'
    return ''.join(random.choice(chars) for _ in range(num_chars))