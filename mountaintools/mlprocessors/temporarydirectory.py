import os
import shutil
import tempfile


class TemporaryDirectory():
    def __init__(self, remove=True, prefix='tmp'):
        self._remove = remove
        self._prefix = prefix

    def __enter__(self) -> str:
        sha1_cache_dir = os.environ.get('SHA1_CACHE_DIR', os.environ.get('KBUCKET_CACHE_DIR', None))
        if sha1_cache_dir:
            dirpath = os.path.join(sha1_cache_dir, 'tmp')
            if not os.path.exists(dirpath):
                os.mkdir(dirpath)
        else:
            dirpath = None
        self._path = str(tempfile.mkdtemp(prefix=self._prefix, dir=dirpath))
        return self._path

    def __exit__(self, exc_type, exc_val, exc_tb):
        if self._remove:
            shutil.rmtree(self._path)

    def path(self):
        return self._path
