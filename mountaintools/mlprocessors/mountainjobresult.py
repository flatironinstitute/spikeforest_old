from copy import deepcopy
import time
from typing import Optional, TYPE_CHECKING
if TYPE_CHECKING:
    # avoid circular dependency
    from .jobqueue import JobQueue


class MountainJobResult():
    def __init__(self, result_object: dict=None, job_queue: Optional['JobQueue']=None):
        self.retcode: Optional[int] = None
        self.timed_out: bool = False
        self.console_out: Optional[str] = None
        self.runtime_info: Optional[dict] = None
        self.outputs: Optional[dict] = None
        self._job_queue: Optional[JobQueue] = job_queue
        self._status: str = 'pending'  # pending, running, finished -- note: finished includes error
        if result_object is not None:
            self.fromObject(result_object)

    def status(self) -> str:
        return self._status

    def isRunning(self) -> bool:
        return self._status == 'running'

    def isFinished(self) -> bool:
        return self._status == 'finished'

    def wait(self, timeout: float=-1) -> bool:
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

    def getObject(self) -> dict:
        return dict(
            retcode=self.retcode,
            timed_out=self.timed_out,
            console_out=self.console_out,
            runtime_info=deepcopy(self.runtime_info),
            outputs=deepcopy(self.outputs)
        )

    def fromObject(self, obj: dict) -> None:
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
