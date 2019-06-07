from copy import deepcopy
import time


class MountainJobResult():
    def __init__(self, result_object=None, job_queue=None):
        self.retcode = None
        self.timed_out = False
        self.console_out = None
        self.runtime_info = None
        self.outputs = None
        self._job_queue = job_queue
        self._status = 'pending'  # pending, running, finished -- note: finished includes error
        if result_object is not None:
            self.fromObject(result_object)

    def status(self):
        return self._status

    def isRunning(self):
        return self._status == 'running'

    def isFinished(self):
        return self._status == 'finished'

    def wait(self, timeout=-1):
        print('.... wait')
        if not self._job_queue:
            return True
        timer = time.time()
        while self._status != 'finished':
            self._job_queue.iterate()
            elapsed = time.time() - timer
            if (timeout >= 0) and (elapsed > timeout):
                return False
            if self._status != 'finished':
                time.sleep(0.2)
        return True

    def getObject(self):
        return dict(
            retcode=self.retcode,
            timed_out=self.timed_out,
            console_out=self.console_out,
            runtime_info=deepcopy(self.runtime_info),
            outputs=deepcopy(self.outputs)
        )

    def fromObject(self, obj):
        if 'retcode' in obj:
            self.retcode = obj['retcode']
        if 'timed_out' in obj:
            self.timed_out = obj['timed_out']
        if 'console_out' in obj:
            self.console_out = obj['console_out']
        if 'runtime_info' in obj:
            self.runtime_info = deepcopy(obj['runtime_info'])
        if 'outputs' in obj:
            self.outputs = deepcopy(obj['outputs'])
