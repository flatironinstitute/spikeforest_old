import json
import urllib.request as request
import hashlib
import os
import pathlib
import random
import base64
import tempfile
from datetime import datetime as dt
from .sha1cache import Sha1Cache
from .cairioremoteclient import CairioRemoteClient
import time
from getpass import getpass


class CairioClient():
    def __init__(self):
        self._default_url = 'https://pairio.org:20443'
        self._remote_config = dict(
            # url='http://localhost:3010',
            url=None,
            collection=None,
            token=None,
            share_id=None,
            alternate_share_ids=None,
            upload_token=None
        )
        self._verbose = False
        self._local_db = CairioLocal()
        self._remote_client = CairioRemoteClient()

    def autoConfig(self, *, collection, key, ask_password=False, password=None):
        if (ask_password) and (password is None):
            password = getpass('Enter password: ')
        config = self.getValue(collection=collection,
                               key=key, password=password)
        if not config:
            raise Exception(
                'Unable to find config ({}.{}). Perhaps a password is incorrect or missing?'.format(collection, key))
        try:
            config = json.loads(config)
        except:
            raise Exception('Error parsing config.')
        self.setRemoteConfig(**config)

    def setRemoteConfig(self, *, url=None, collection=None, token=None, share_id=None, upload_token=None, alternate_share_ids=None):
        if url is not None:
            self._remote_config['url'] = url
        if collection is not None:
            self._remote_config['collection'] = collection
        if token is not None:
            self._remote_config['token'] = token
        if share_id is not None:
            self._remote_config['share_id'] = share_id
        if alternate_share_ids is not None:
            self._remote_config['alternate_share_ids'] = alternate_share_ids
        if upload_token is not None:
            self._remote_config['upload_token'] = upload_token

        c = self._remote_config
        if c['collection'] and c['token']:
            config1 = 'remote database {} (readwrite)'.format(c['collection'])
        elif c['collection'] and (not c['token']):
            config1 = 'remote database {} (readonly)'.format(c['collection'])
        else:
            config1 = 'local database'

        if c['share_id'] and c['upload_token']:
            config2 = 'remote kb-share {} (readwrite)'.format(c['share_id'])
        elif c['share_id'] and (not c['upload_token']):
            config2 = 'remote kb-share {} (readonly)'.format(c['share_id'])
        else:
            config2 = 'local sha-1 cache'

        print('CAIRIO CONFIG: {}; {}'.format(config1, config2))
        if c['alternate_share_ids']:
            print('Alternate share ids:', c['alternate_share_ids'])

    def getRemoteConfig(self):
        ret = self._remote_config.copy()
        return ret

    def addRemoteCollection(self, collection, token, admin_token):
        return self._remote_client.addCollection(collection=collection, token=token, url=self._remote_config.get('url') or self._default_url, admin_token=admin_token)

    # get value / set value
    def getValue(self, *, key, subkey=None, password=None, parse_json=False, collection=None):
        ret = self._get_value(key=key, subkey=subkey,
                              password=password, collection=collection)
        if parse_json and ret:
            try:
                ret = json.loads(ret)
            except:
                print('Warning: Problem parsing json in cairio.getValue()')
                return None
        return ret

    def setValue(self, *, key, subkey=None, value, overwrite=True, password=None):
        return self._set_value(key=key, subkey=subkey, value=value, overwrite=overwrite, password=password)

    def getSubKeys(self, key, password=None):
        return list(self._get_sub_keys(key=key, password=password))

    # realize file / save file
    def realizeFile(self, path=None, *, key=None, subkey=None, password=None, share_id=None):
        if path is not None:
            return self._realize_file(path=path, share_id=share_id)
        elif key is not None:
            val = self.getValue(key=key, subkey=subkey, password=password)
            if not val:
                return None
            return self.realizeFile(path=val, share_id=share_id)
        else:
            raise Exception('Missing key or path in realizeFile().')

    def saveFile(self, path=None, *, key=None, subkey=None, basename=None, password=None, confirm=False):
        if path is None:
            self.setValue(key=key, subkey=subkey,
                          value=None, password=password)
            return None
        sha1_path = self._save_file(
            path=path, basename=basename, confirm=confirm)
        if key is not None:
            self.setValue(key=key, subkey=subkey,
                          value=sha1_path, password=password)
        return sha1_path

    # load object / save object
    def loadObject(self, *, key=None, path=None, subkey=None, password=None):
        txt = self.loadText(key=key, path=path,
                            subkey=subkey, password=password)
        if txt is None:
            return None
        return json.loads(txt)

    def saveObject(self, object, *, key=None, subkey=None, basename='object.json', password=None, confirm=False):
        if object is None:
            self.setValue(key=key, subkey=subkey,
                          value=None, password=password)
            return None
        return self.saveText(text=json.dumps(object), key=key, subkey=subkey, basename=basename, password=password, confirm=confirm)

    # load text / save text
    def loadText(self, *, key=None, path=None, subkey=None, password=None):
        fname = self.realizeFile(
            key=key, path=path, subkey=subkey, password=password)
        if fname is None:
            return None
        try:
            with open(fname) as f:
                return f.read()
        except:
            print('Unexpected problem reading file in loadText: '+fname)
            return None

    def saveText(self, text, *, key=None, subkey=None, basename='file.txt', password=None, confirm=False):
        if text is None:
            self.setValue(key=key, subkey=subkey,
                          value=None, password=password)
            return None
        tmp_fname = _create_temporary_file_for_text(text=text)
        try:
            ret = self.saveFile(tmp_fname, key=key, subkey=subkey,
                                basename=basename, password=password, confirm=confirm)
        except:
            os.unlink(tmp_fname)
            raise
        os.unlink(tmp_fname)
        return ret

    def readDir(self, path, recursive=False, include_sha1=True):
        if path.startswith('kbucket://'):
            list0 = path.split('/')
            share_id = list0[2]
            path0 = '/'.join(list0[3:])
            ret = self._read_kbucket_dir(
                share_id=share_id, path=path0, recursive=recursive, include_sha1=include_sha1)
        else:
            ret = self._read_file_system_dir(
                path=path, recursive=recursive, include_sha1=include_sha1)
        return ret

    def computeDirHash(self, path):
        dd = self.readDir(path=path, recursive=True, include_sha1=True)
        return _sha1_of_object(dd)

    def computeFileSha1(self, path):
        if path.startswith('sha1://'):
            list0 = path.split('/')
            sha1 = list0[2]
            return sha1
        elif path.startswith('kbucket://'):
            sha1, size, url = self._local_db.getKBucketFileInfo(path=path)
            return sha1
        else:
            return self._local_db.computeFileSha1(path)

    def localCacheDir(self):
        return self._local_db.localCacheDir()

    def findFileBySha1(self, *, sha1, share_id=None):
        return self._realize_file(path='sha1://'+sha1, resolve_locally=False, share_id=share_id)

    def findFile(self, path, local_only=False, share_id=None):
        return self._realize_file(path=path, resolve_locally=False, local_only=local_only, share_id=share_id)

    def moveToLocalCache(self, path, basename=None):
        return self._save_file(path=path, prevent_upload=True, return_sha1_url=False, basename=basename)

    def _get_value(self, *, key, subkey, password=None, collection=None):
        if password is not None:
            key = dict(key=key, password=password)
        if collection is None:
            collection = self._remote_config['collection']
        if collection:
            return self._remote_client.getValue(key=key, subkey=subkey, collection=collection, url=self._remote_config.get('url') or self._default_url)
        return self._local_db.getValue(key=key, subkey=subkey)

    def _set_value(self, *, key, subkey, value, overwrite, password=None):
        if password is not None:
            key = dict(key=key, password=password)
        collection = self._remote_config['collection']
        if collection:
            return self._remote_client.setValue(key=key, subkey=subkey, value=value, overwrite=overwrite, collection=collection, url=self._remote_config.get('url') or self._default_url, token=self._remote_config['token'])
        return self._local_db.setValue(key=key, subkey=subkey, value=value, overwrite=overwrite)

    def _get_sub_keys(self, *, key, password=None):
        if password is not None:
            key = dict(key=key, password=password)
        collection = self._remote_config['collection']
        if collection:
            return self._remote_client.getSubKeys(key=key)
        return self._local_db.getSubKeys(key=key)

    def _realize_file(self, *, path, resolve_locally=True, local_only=False, share_id=None):
        ret = self._local_db.realizeFile(path=path, local_only=local_only)
        if ret:
            return ret
        if local_only:
            return None
        if share_id is not None:
            share_ids = [share_id]
        else:
            if self._remote_config['share_id'] is not None:
                share_ids = [self._remote_config['share_id']]
            else:
                share_ids = []
            if self._remote_config['alternate_share_ids'] is not None:
                share_ids = share_ids + \
                    self._remote_config['alternate_share_ids']
        for share_id0 in share_ids:
            if path.startswith('sha1://'):
                list0 = path.split('/')
                sha1 = list0[2]
                url, size = self._find_on_kbucket(
                    share_id=share_id0, sha1=sha1)
                if url:
                    if resolve_locally:
                        return self._local_db.realizeFileFromUrl(url=url, sha1=sha1, size=size)
                    else:
                        return url
        return None

    def _save_file(self, *, path, basename, confirm=False, prevent_upload=False, return_sha1_url=True):
        path = self.realizeFile(path)
        if not path:
            return False
        ret = self._local_db.saveFile(
            path=path, basename=basename, return_sha1_url=return_sha1_url)
        if not ret:
            return False
        share_id = self._remote_config['share_id']
        upload_token = self._remote_config['upload_token']
        if (share_id) and (upload_token) and (not prevent_upload):
            sha1 = self.computeFileSha1(path=path)
            if sha1:
                url, _ = self._find_on_kbucket(share_id=share_id, sha1=sha1)
                if not url:
                    cas_upload_server_url = self._get_cas_upload_server_url_for_share(
                        share_id=share_id)
                    if cas_upload_server_url:
                        if self._remote_client.uploadFile(path=path, sha1=sha1, cas_upload_server_url=cas_upload_server_url, upload_token=upload_token):
                            if confirm:
                                self._wait_until_found_on_kbucket(
                                    share_id=share_id, sha1=sha1)
        return ret

    def _wait_until_found_on_kbucket(self, *, share_id, sha1):
        timer = time.time()
        wait_str = 'Waiting until file is on kbucket {} (sha1={})'.format(
            share_id, sha1)
        if self._wait_until_found_on_kbucket_helper(share_id=share_id, sha1=sha1, num_retries=2, delay_sec=1):
            print('File is on kbucket: {}'.format(sha1))
            return True
        print(wait_str)
        if self._wait_until_found_on_kbucket_helper(share_id=share_id, sha1=sha1, num_retries=10, delay_sec=2):
            print('File is on kbucket: {}'.format(sha1))
            return True
        print(wait_str)
        if self._wait_until_found_on_kbucket_helper(share_id=share_id, sha1=sha1, num_retries=10, delay_sec=4):
            print('File is on kbucket: {}'.format(sha1))
            return True
        raise Exception('Unable to find file {} on kbucket after waiting for {} seconds.'.format(sha1,
                                                                                                 time.time()-timer))

    def _wait_until_found_on_kbucket_helper(self, *, share_id, sha1, num_retries, delay_sec):
        for retry in range(1, num_retries+1):
            url, _ = self._find_on_kbucket(share_id=share_id, sha1=sha1)
            if url:
                return True
            time.sleep(delay_sec)
        return False

    def _find_on_kbucket(self, *, share_id, sha1):
        kbucket_url = self._local_db.kbucketUrl()
        if not kbucket_url:
            return (None, None)
        url = kbucket_url+'/'+share_id+'/api/find/'+sha1
        obj = _http_get_json(url)
        if not obj:
            return (None, None)
        if not obj['success']:
            return (None, None)
        if not obj['found']:
            return (None, None)
        try:
            size = obj['results'][0]['size']
        except:
            size = 0
        urls = obj['urls']
        node_info = self._local_db.getNodeInfo(share_id=share_id)
        if node_info and node_info['accessible']:
            for url0 in urls:
                if url0.startswith(node_info['listen_url']):
                    return (url0, size)
        for url0 in urls:
            if url0.startswith(self._local_db.kbucketUrl()):
                return (url0, size)
        return (None, None)

    def _get_cas_upload_server_url_for_share(self, share_id):
        node_info = self._local_db.getNodeInfo(share_id=share_id)
        if not node_info:
            print('Warning: Unable to get node info for share: '+share_id)
            return None
        if 'cas_upload_url' not in node_info:
            print(
                'Warning: node_info does not have info.cas_upload_url field for share: '+share_id)
        return node_info.get('cas_upload_url', None)

    def _read_kbucket_dir(self, *, share_id, path, recursive, include_sha1):
        url = self._local_db.kbucketUrl()+'/'+share_id+'/api/readdir/'+path
        obj = _http_get_json(url)
        if (not obj) or (not obj['success']):
            return None

        ret = dict(
            files={},
            dirs={}
        )
        for file0 in obj['files']:
            name0 = file0['name']
            ret['files'][name0] = dict(
                size=file0['size']
            )
            if include_sha1:
                if 'prv' in file0:
                    ret['files'][name0]['sha1'] = file0['prv']['original_checksum']
        for dir0 in obj['dirs']:
            name0 = dir0['name']
            ret['dirs'][name0] = {}
            if recursive:
                ret['dirs'][name0] = _read_kbucket_dir(path+'/'+name0)
        return ret

    def _read_file_system_dir(self, *, path, recursive, include_sha1):
        ret = dict(
            files={},
            dirs={}
        )
        list0 = _safe_list_dir(path)
        for name0 in list0:
            path0 = path+'/'+name0
            if os.path.isfile(path0):
                ret['files'][name0] = dict(
                    size=os.path.getsize(path0)
                )
                if include_sha1:
                    ret['files'][name0]['sha1'] = self.computeFileSha1(path0)
            elif os.path.isdir(path0):
                ret['dirs'][name0] = {}
                if recursive:
                    ret['dirs'][name0] = self._read_file_system_dir(
                        path=path0, recursive=recursive, include_sha1=include_sha1)
        return ret


class CairioLocal():
    def __init__(self):
        self._local_database_path = _get_default_local_db_path()
        self._sha1_cache = Sha1Cache()
        local_cache_dir = os.getenv('KBUCKET_CACHE_DIR', '/tmp/sha1-cache')
        self._sha1_cache.setDirectory(local_cache_dir)
        self._kbucket_url = os.getenv(
            'KBUCKET_URL', 'https://kbucket.flatironinstitute.org')
        self._nodeinfo_cache = dict()

    def getValue(self, *, key, subkey=None):
        if subkey is not None:
            val = self.getValue(key=dict(subkeys=True, key=key))
            try:
                val = json.loads(val)
            except:
                val = None
            if val is None:
                val = dict()
            if subkey == '-':
                return json.dumps(val)
            return val.get(subkey, None)
        keyhash = _hash_of_key(key)
        db_path = self._get_db_path_for_keyhash(keyhash)
        db = _db_load(db_path)
        doc = db.get(keyhash, None)
        if doc:
            return doc.get('value')
        else:
            return None

    def setValue(self, *, key, subkey, value, overwrite):
        if subkey is not None:
            val = self.getValue(key=dict(subkeys=True, key=key))
            try:
                val = json.loads(val)
            except:
                val = None
            if val is None:
                val = dict()
            if value is not None:
                val[subkey] = value
            else:
                if subkey in val:
                    del val[subkey]
            return self.setValue(key=dict(subkeys=True,key=key), value=json.dumps(val), subkey=None, overwrite=overwrite)
        keyhash = _hash_of_key(key)
        db_path = self._get_db_path_for_keyhash(keyhash)
        db = _db_load(db_path)
        doc = db.get(keyhash, None)
        if doc is None:
            doc = dict()
        if value is not None:
            doc['value'] = value
            db[keyhash] = doc
        else:
            if keyhash in db:
                del db[keyhash]
        _db_save(db_path, db)
        return True

    def getSubKeys(self, *, key):
        val = self.getValue(key=key, subkey=None)
        try:
            val = json.loads(val)
            return list(val.keys())
        except:
            return []

    def realizeFile(self, *, path, local_only=False):
        if path.startswith('sha1://'):
            list0 = path.split('/')
            sha1 = list0[2]
            return self._realize_file_from_sha1(sha1=sha1)
        elif path.startswith('kbucket://'):
            sha1, size, url = self._get_kbucket_file_info(path=path)
            if sha1 is None:
                return None
            try_local_path = self._sha1_cache.findFile(sha1)
            if try_local_path is not None:
                return try_local_path
            if local_only:
                return None
            return self._sha1_cache.downloadFile(url=url, sha1=sha1, size=size)

        # If the file exists on the local computer, just use that
        if os.path.exists(path):
            return os.path.abspath(path)

        return None

    def realizeFileFromUrl(self, *, url, sha1, size):
        return self._sha1_cache.downloadFile(url=url, sha1=sha1, size=size)

    def saveFile(self, *, path, basename, return_sha1_url=True):
        if basename is None:
            basename = os.path.basename(path)

        path0 = path
        path = self.realizeFile(path=path0)
        if not path:
            raise Exception('Unable to realize file in saveFile: '+path0)

        local_path, sha1 = self._sha1_cache.copyFileToCache(path)

        if sha1 is None:
            raise Exception('Unable to copy file to cache in saveFile: '+path0)

        if not return_sha1_url:
            return local_path

        ret_path = 'sha1://{}/{}'.format(sha1, basename)
        return ret_path

    def computeFileSha1(self, path):
        return self._sha1_cache.computeFileSha1(path=path)

    def getNodeInfo(self, *, share_id):
        return self._get_node_info(share_id=share_id)

    def getKBucketUrlForShare(self, *, share_id):
        return self._get_kbucket_url_for_share(share_id=share_id)

    def kbucketUrl(self):
        return self._kbucket_url

    def localCacheDir(self):
        return self._sha1_cache.directory()

    def _get_db_path_for_keyhash(self, keyhash):
        return self._local_database_path+'/{}/{}.db'.format(keyhash[0], keyhash[1:3])

    def _realize_file_from_sha1(self, *, sha1):
        fname = self._sha1_cache.findFile(sha1)
        if fname is not None:
            return os.path.abspath(fname)
        return None

    def _get_node_info(self, *, share_id):
        if share_id in self._nodeinfo_cache:
            node_info = self._nodeinfo_cache[share_id]
        else:
            url = self._kbucket_url+'/'+share_id+'/api/nodeinfo'
            obj = _http_get_json(url)
            if not obj:
                print('Warning: unable to find node info for share {}'.format(share_id))
                return None
            if 'info' not in obj:
                print(
                    'Warning: info not found in node info object for share {}'.format(share_id))
                return None
            node_info = obj['info']
        if node_info:
            self._nodeinfo_cache[share_id] = node_info
            if 'accessible' not in node_info:
                url00 = node_info.get('listen_url', '') + \
                    '/'+share_id+'/api/nodeinfo'
                print(
                    'Testing whether share {} is directly accessible...'.format(share_id))
                node_info['accessible'] = _test_url_accessible(
                    url00, timeout=2)
                if node_info['accessible']:
                    print('Share {} is directly accessible.'.format(share_id))
                else:
                    print('Share {} is not directly accessible.'.format(share_id))
        return node_info

    def _get_kbucket_url_for_share(self, *, share_id):
        node_info = self._get_node_info(share_id=share_id)
        if (node_info) and (node_info['accessible']):
            return node_info.get('listen_url', None)
        else:
            # TODO: check the parent hub, etc before jumping right to the top
            return self._kbucket_url

    def getKBucketFileInfo(self, *, path):
        return self._get_kbucket_file_info(path=path)

    def _get_kbucket_file_info(self, *, path):
        list0 = path.split('/')
        kbshare_id = list0[2]
        path0 = '/'.join(list0[3:])

        kbucket_url = self._get_kbucket_url_for_share(share_id=kbshare_id)
        if not kbucket_url:
            return (None, None, None)

        url_prv = kbucket_url+'/'+kbshare_id+'/prv/'+path0
        try:
            prv = _http_get_json(url_prv)
        except:
            return (None, None, None)

        if prv is None:
            return (None, None, None)
        try:
            sha1 = prv['original_checksum']
            size = prv['original_size']
        except:
            return (None, None, None)
        if not sha1:
            return (None, None, None)

        url_download = kbucket_url+'/'+kbshare_id+'/download/'+path0
        return (sha1, size, url_download)


def _http_get_json(url, verbose=False, num_http_retries=2):
    if verbose:
        print('_http_get_json::: '+url)
    try:
        req = request.urlopen(url)
    except:
        if num_http_retries > 0:
            print('Retrying http request to: '+url)
            return _http_get_json(url, verbose=verbose,
                                  num_http_retries=num_http_retries-1)
        else:
            raise Exception('Unable to open url: '+url)
    try:
        ret = json.load(req)
    except:
        raise Exception('Unable to load json from url: '+url)
    if verbose:
        print(ret)
        print('done.')
    return ret


# TODO: make this thread-safe
def _db_load(path):
    try:
        db = _read_json_file(path)
    except:
        db = dict()
    return db


def _db_save(path, db):
    _write_json_file(db, path)


def _read_json_file(path):
    with open(path) as f:
        return json.load(f)


def _write_json_file(obj, path):
    with open(path, 'w') as f:
        return json.dump(obj, f)


def _get_default_local_db_path():
    dirname = str(pathlib.Path.home())+'/.cairio'
    if not os.path.exists(dirname):
        os.mkdir(dirname)
    ret = dirname+'/database'
    if not os.path.exists(ret):
        os.mkdir(ret)
    for n in range(16):
        subdir = ret+'/'+hex(n)[2:]
        if not os.path.exists(subdir):
            os.mkdir(subdir)
    return ret


def _hash_of_key(key):
    if (type(key) == dict) or (type(key) == list):
        key = json.dumps(key, sort_keys=True, separators=(',', ':'))
    return _sha1_of_string(key)


def _sha1_of_string(txt):
    hh = hashlib.sha1(txt.encode('utf-8'))
    ret = hh.hexdigest()
    return ret


def _sha1_of_object(obj):
    txt = json.dumps(obj, sort_keys=True, separators=(',', ':'))
    return _sha1_of_string(txt)


def _create_temporary_file_for_text(*, text):
    tmp_fname = _create_temporary_fname('.txt')
    with open(tmp_fname, 'w') as f:
        f.write(text)
    return tmp_fname


def _create_temporary_fname(ext):
    tempdir = os.environ.get('KBUCKET_CACHE_DIR', tempfile.gettempdir())
    return tempdir+'/tmp_cairioclient_'+''.join(random.choices('abcdefghijklmnopqrstuvwxyz', k=10))+ext


def _test_url_accessible(url, timeout):
    try:
        req = request.Request(url, method="HEAD")
        code = request.urlopen(req, timeout=timeout).getcode()
        return (code == 200)
    except:
        return False


def _safe_list_dir(path):
    try:
        ret = os.listdir(path)
        return ret
    except:
        print('Warning: unable to listdir: '+path)
        return []


# The global module client
client = CairioClient()

if os.environ.get('CAIRIO_CONFIG'):
    print('configuring cairio...')
    a = os.environ.get('CAIRIO_CONFIG').split('.')
    password = os.environ.get('CAIRIO_CONFIG_PASSWORD', None)
    client.autoConfig(collection=a[0], key=a[1], password=password)
if os.environ.get('CAIRIO_ALTERNATE_SHARE_IDS'):
    tmp = os.environ.get('CAIRIO_ALTERNATE_SHARE_IDS')
    list0 = tmp.split(',')
    client.setRemoteConfig(alternate_share_ids=list0)
