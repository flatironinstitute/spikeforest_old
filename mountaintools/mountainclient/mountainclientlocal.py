import os
import json
import shutil
import mtlogging
import pathlib
from .sha1cache import Sha1Cache
from .filelock import FileLock
from typing import Union, List, Optional
from .mttyping import StrOrDict
from .aux import _read_text_file, _write_text_file, _sha1_of_string


class MountainClientLocal():
    def __init__(self, parent):
        self._parent = parent
        self._sha1_cache = Sha1Cache()
        self._kbucket_url = os.getenv(
            'KBUCKET_URL', 'https://kbucket.flatironinstitute.org')
        self._nodeinfo_cache = dict()
        self._verbose = None

    def configVerbose(self, value: bool) -> None:
        self._verbose = value

    def getSubKeys(self, *, key: Union[str, dict]) -> Optional[List[str]]:
        keyhash = _hash_of_key(key)
        subkey_db_path = self._get_subkey_file_path_for_keyhash(
            keyhash, _create=False)
        if not os.path.exists(subkey_db_path):
            return []
        ret = []
        with FileLock(subkey_db_path + '.lock', exclusive=False):
            list0 = _safe_list_dir(subkey_db_path)
            if list0 is None:
                return None
            for name0 in list0:
                if name0.endswith('.txt'):
                    ret.append(name0[0:-4])
        return ret

    def getValue(self, *, key: StrOrDict, subkey: Optional[str]=None, check_alt=False, _db_path: Optional[str]=None, _disable_lock: bool=False) -> Optional[str]:
        keyhash = _hash_of_key(key)
        if subkey is not None:
            if check_alt:
                raise Exception('Cannot use check_alt together with subkey.')
            if subkey == '-':
                subkeys = self.getSubKeys(key=key)
                if subkeys is None:
                    return '{}'
                obj = dict()
                for subkey in subkeys:
                    val = self.getValue(key=key, subkey=subkey)
                    if val is not None:
                        obj[subkey] = val
                return json.dumps(obj)
            else:
                subkey_db_path = self._get_subkey_file_path_for_keyhash(
                    keyhash, _db_path=_db_path, _create=False)
                fname0 = os.path.join(subkey_db_path, subkey + '.txt')
                if not os.path.exists(fname0):
                    return None
                with FileLock(subkey_db_path + '.lock', _disable_lock=_disable_lock, exclusive=False):
                    txt = _read_text_file(fname0)
                    return txt
        else:
            # not a subkey
            db_path = self._get_file_path_for_keyhash(
                keyhash, _db_path=_db_path, _create=False)
            fname0 = db_path
            if not os.path.exists(fname0):
                if check_alt:
                    alternate_db_paths = self.alternateLocalDatabasePaths()
                    for db_path in alternate_db_paths:
                        val = self.getValue(
                            key=key, subkey=None, check_alt=None, _db_path=db_path, _disable_lock=True)
                        if val:
                            return val
                return None
            with FileLock(fname0 + '.lock', _disable_lock=_disable_lock, exclusive=False):
                txt = _read_text_file(fname0)
                return txt

    def setValue(self, *, key: StrOrDict, subkey: Optional[str], value: Union[str, None], overwrite: bool) -> bool:
        keyhash = _hash_of_key(key)
        if subkey is not None:
            if subkey == '-':
                if value is not None:
                    raise Exception(
                        'Cannot set all subkeys with value that is not None')
                subkey_db_path = self._get_subkey_file_path_for_keyhash(
                    keyhash, _create=True)
                with FileLock(subkey_db_path + '.lock', exclusive=True):
                    shutil.rmtree(subkey_db_path)
            else:
                subkey_db_path = self._get_subkey_file_path_for_keyhash(
                    keyhash, _create=True)
                fname0 = os.path.join(subkey_db_path, subkey + '.txt')
                if os.path.exists(fname0):
                    if not overwrite:
                        return False
                with FileLock(subkey_db_path + '.lock', exclusive=True):
                    if os.path.exists(fname0):
                        if not overwrite:
                            return False
                    if value is None:
                        os.unlink(fname0)
                    else:
                        # _write_text_file_safe(fname0, value)
                        _write_text_file(fname0, value)
        else:
            # not a subkey
            db_path = self._get_file_path_for_keyhash(keyhash, _create=True)
            fname0 = db_path
            if os.path.exists(fname0):
                if not overwrite:
                    return False
            with FileLock(fname0 + '.lock', exclusive=True):
                if os.path.exists(fname0):
                    if not overwrite:
                        return False
                if value is None:
                    if os.path.exists(fname0):
                        os.unlink(fname0)
                else:
                    _write_text_file(fname0, value)
        return True

    def realizeFile(self, *, path: str, local_only: bool=False, resolve_locally: bool=True, dest_path: Optional[str]=None, show_progress: bool=False) -> Optional[str]:
        if path.startswith('sha1://'):
            list0 = path.split('/')
            sha1 = list0[2]
            return self._realize_file_from_sha1(sha1=sha1, dest_path=dest_path, show_progress=show_progress)
        elif path.startswith('sha1dir://'):
            sha1 = self.computeFileSha1(path=path)
            if not sha1:
                return None
            return self._parent._realize_file(path='sha1://' + sha1, local_only=local_only, resolve_locally=resolve_locally, dest_path=dest_path, show_progress=show_progress)

        # If the file exists on the local computer, just use that
        if os.path.isfile(path):
            if (dest_path is not None) and (os.path.abspath(path) != os.path.abspath(dest_path)):
                if show_progress:
                    print('Copying file {} -> {}'.format(path, dest_path))
                shutil.copyfile(path, dest_path)
                return os.path.abspath(dest_path)
            return os.path.abspath(path)

        return None

    def realizeFileFromUrl(self, *, url: str, sha1: str, size: int, dest_path: Optional[str]=None, show_progress=False) -> Optional[str]:
        return self._sha1_cache.downloadFile(url=url, sha1=sha1, size=size, target_path=dest_path, show_progress=show_progress)

    @mtlogging.log()
    def saveFile(self, *, path: str, basename: Optional[str], return_sha1_url: bool=True) -> Optional[str]:
        if basename is None:
            basename = os.path.basename(path)

        path0 = path
        path_realized = self.realizeFile(path=path0)
        if not path_realized:
            raise Exception('Unable to realize file in saveFile: ' + path0)
        path = str(path_realized)

        local_path, sha1 = self._sha1_cache.copyFileToCache(path)

        if sha1 is None:
            raise Exception(
                'Unable to copy file to cache in saveFile: ' + path0)

        if not return_sha1_url:
            return local_path

        if basename:
            ret_path = 'sha1://{}/{}'.format(sha1, basename)
        else:
            ret_path = 'sha1://{}'.format(sha1)
        return ret_path

    @mtlogging.log(name='MountainClientLocal:computeFileSha1')
    def computeFileSha1(self, path: str, _cache_only: bool=False) -> Optional[str]:
        if path.startswith('kbucket://'):
            raise Exception('kucket:// paths are no longer supported')

        if path.startswith('sha1://'):
            list0 = path.split('/')
            sha1 = list0[2]
            return sha1
        elif path.startswith('sha1dir://'):
            if _cache_only:
                return None
            list0 = path.split('/')
            sha1 = list0[2]
            if '.' in sha1:
                sha1 = sha1.split('.')[0]
            dd = self._parent.loadObject(path='sha1://' + sha1)
            if not dd:
                return None
            ii = 3
            while ii < len(list0):
                name0 = list0[ii]
                if name0 in dd['dirs']:
                    dd = dd['dirs'][name0]
                elif name0 in dd['files']:
                    if ii + 1 == len(list0):
                        sha1 = dd['files'][name0]['sha1']
                        return sha1
                    else:
                        return None
                else:
                    return None
                ii = ii + 1
            return None
        else:
            return self._sha1_cache.computeFileSha1(path=path, _cache_only=_cache_only)

    def localCacheDir(self) -> str:
        return self._sha1_cache.directory()

    def alternateLocalCacheDirs(self) -> List[str]:
        return self._sha1_cache.alternateDirectories()

    def localDatabasePath(self) -> str:
        return _get_default_local_db_path()

    def alternateLocalDatabasePaths(self) -> List[str]:
        return _get_default_alternate_local_db_paths()

    def _get_file_path_for_keyhash(self, keyhash: str, *, _create: bool, _db_path: Optional[str]=None) -> str:
        if _db_path:
            database_path = _db_path
        else:
            database_path = self.localDatabasePath()
        path = os.path.join(database_path, keyhash[0:2], keyhash[2:4])
        if _create:
            if not os.path.exists(path):
                try:
                    os.makedirs(path)
                except:
                    if not os.path.exists(path):
                        raise Exception(
                            'Unexpected problem. Unable to create directory: ' + path)
        return os.path.join(path, keyhash)

    def _get_subkey_file_path_for_keyhash(self, keyhash: str, *, _create: bool, _db_path: Optional[str]=None) -> str:
        if _db_path:
            database_path = _db_path
        else:
            database_path = self.localDatabasePath()
        path = os.path.join(
            database_path, keyhash[0:2], keyhash[2:4], keyhash + '.dir')
        if _create:
            if not os.path.exists(path):
                try:
                    os.makedirs(path)
                except:
                    if not os.path.exists(path):
                        raise Exception(
                            'Unexpected problem. Unable to create directory: ' + path)
        return path

    def _realize_file_from_sha1(self, *, sha1: str, dest_path: Optional[str]=None, show_progress: bool=False) -> Optional[str]:
        # try to find the file in cache
        fname = self._sha1_cache.findFile(sha1)
        if fname is not None:
            if (dest_path is not None) and (os.path.abspath(fname) != os.path.abspath(dest_path)):
                if os.path.exists(dest_path):
                    already_there = False
                    if os.path.getsize(dest_path) == os.path.getsize(fname):
                        # there is a chance they are the same
                        if self.computeFileSha1(dest_path, _cache_only=True) == sha1:
                            # already exists at destination
                            already_there = True
                else:
                    already_there = False
                if not already_there:
                    if show_progress:
                        print('Copying file {} -> {}'.format(fname, dest_path))
                    shutil.copyfile(fname, dest_path)
                    self._sha1_cache.reportFileSha1(dest_path, sha1)
                return os.path.abspath(dest_path)
            return os.path.abspath(fname)
        return None


def _get_default_local_db_path() -> str:
    dir_old = str(pathlib.Path.home()) + '/.cairio'
    dir_new = str(pathlib.Path.home()) + '/.mountain'
    if os.path.exists(dir_old) and (not os.path.exists(dir_new)):
        print('Moving config directory: {} -> {}'.format(dir_old, dir_new))
        shutil.move(dir_old, dir_new)
    default_dirname = dir_new
    dirname = os.environ.get(
        'MOUNTAIN_DIR', os.environ.get('CAIRIO_DIR', default_dirname))
    if not os.path.exists(dirname):
        try:
            os.mkdir(dirname)
        except:
            # maybe it was created in a different process
            if not os.path.exists(dirname):
                raise
    ret = dirname + '/database'
    return ret


def _get_default_alternate_local_db_paths() -> List[str]:
    val = os.environ.get('MOUNTAIN_DIR_ALT', None)
    if not val:
        return []
    dirnames = val.split(':')
    return [dirname + '/database' for dirname in dirnames]


def _hash_of_key(key: StrOrDict) -> str:
    if (type(key) == dict) or (type(key) == list):
        key2 = json.dumps(key, sort_keys=True, separators=(',', ':'))
        return _sha1_of_string(key2)
    else:
        if str(key).startswith('~'):
            return str(key)[1:]
        else:
            return _sha1_of_string(str(key))


def _safe_list_dir(path: str) -> Optional[List[str]]:
    try:
        ret = os.listdir(path)
        return ret
    except:
        return None
