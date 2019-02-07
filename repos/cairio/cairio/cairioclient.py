import json
import urllib.request as request
import hashlib
import os
import pathlib
import random
import fasteners
import base64
import tempfile
from datetime import datetime as dt
from .sha1cache import Sha1Cache

class CairioClient():
    def __init__(self):
        self._config = dict(
        )
        self._verbose = False
        self._local_db=CairioLocal()

    def setConfig(self):
        pass

    def getConfig(self):
        ret = self._config.copy()
        return ret


    # get value / set value
    def getValue(self,*,key,subkey=None):
        return self._get_value(key=key,subkey=subkey)

    def setValue(self,*,key,subkey=None,value,overwrite=True):
        return self._set_value(key=key,subkey=subkey,value=value,overwrite=overwrite)

    def getSubKeys(self,key):
        return list(self._get_sub_keys(key=key))

    # realize file / save file
    def realizeFile(self,key_or_path=None,*,key=None,path=None,subkey=None):
        if key_or_path is None:
            if key:
                key_or_path=key
            if path:
                key_or_path=path
        else:
            if key or path:
                raise Exception('Invalid call to realizeFile.')

        if type(key_or_path)==str:
            path=key_or_path
            return self._realize_file(path=path)
        elif type(key_or_path)==dict:
            key=key_or_path
            val=self.getValue(key=key,subkey=subkey)
            if not val:
                return None
            return self.realizeFile(path=val)
        else:
            raise Exception('Invalid type for key_or_path in realizeFile.',type(key_or_path))

    def saveFile(self,path,*,key=None,subkey=None,basename=None):
        if path is None:
            self.setValue(key=key,subkey=subkey,value=None)
            return None
        sha1_path=self._save_file(path=path,basename=basename)
        if key is not None:
            self.setValue(key=key,subkey=subkey,value=sha1_path)
        return sha1_path


    # load object / save object
    def loadObject(self,key_or_path=None,*,key=None,path=None,subkey=None):
        if key_or_path is None:
            if key:
                key_or_path=key
            if path:
                key_or_path=path
        else:
            if key or path:
                raise Exception('Invalid call to loadObject.')

        txt=self.loadText(key_or_path=key_or_path,subkey=subkey)
        if txt is None:
            return None
        return json.loads(txt)

    def saveObject(self,object,*,key=None,subkey=None,basename='object.json'):
        if object is None:
            self.setValue(key=key,subkey=subkey,value=None)
            return None
        return self.saveText(text=json.dumps(object),key=key,subkey=subkey,basename=basename)

    # load text / save text
    def loadText(self,key_or_path=None,*,key=None,path=None,subkey=None):
        if key_or_path is None:
            if key:
                key_or_path=key
            if path:
                key_or_path=path
        else:
            if key or path:
                raise Exception('Invalid call to loadText.')

        fname=self.realizeFile(key_or_path=key_or_path,subkey=subkey)
        if fname is None:
            return None
        with open(fname) as f:
            return f.read()

    def saveText(self,text,*,key=None,subkey=None,basename='file.txt'):
        if text is None:
            self.setValue(key=key,subkey=subkey,value=None)
            return None
        tmp_fname=_create_temporary_file_for_text(text=text)
        try:
            ret=self.saveFile(tmp_fname,key=key,subkey=subkey,basename=basename)
        except:
            os.unlink(tmp_fname)
            raise
        os.unlink(tmp_fname)
        return ret

    def _get_value(self,*,key,subkey):
        return self._local_db.getValue(key=key,subkey=subkey)

    def _set_value(self,*,key,subkey,value,overwrite):
        return self._local_db.setValue(key=key,subkey=subkey,value=value,overwrite=overwrite)

    def _get_sub_keys(self,*,key):
        return self._local_db.getSubKeys(key=key)

    def _realize_file(self,*,path):
        return self._local_db.realizeFile(path=path)

    def _save_file(self,*,path,basename):
        return self._local_db.saveFile(path=path,basename=basename)

class CairioLocal():
    def __init__(self):
        self._local_database_path=_get_default_local_db_path()
        self._sha1_cache=Sha1Cache()
        local_cache_dir=os.getenv('KBUCKET_CACHE_DIR', '/tmp/sha1-cache')
        self._sha1_cache.setDirectory(local_cache_dir)
        self._kbucket_url=os.getenv('KBUCKET_URL', 'https://kbucket.flatironinstitute.org')
        self._nodeinfo_cache=dict()

    def getValue(self,*,key,subkey=None):
        if subkey is not None:
            val=self.getValue(key=key,subkey=None)
            try:
                val=json.loads(val)
                return val.get(subkey,None)
            except:
                return None
        keyhash=_hash_of_key(key)
        db_path=self._get_db_path_for_keyhash(keyhash)
        db = _db_load(db_path)
        doc = db.get(keyhash, None)
        if doc:
            return doc.get('value')
        else:
            return None

    def setValue(self,*,key,subkey,value,overwrite):
        if subkey is not None:
            val=self.getValue(key=key)
            try:
                val=json.loads(val)
            except:
                val=None
            if val is None:
                val=dict()
            if value is not None:
                val[subkey]=value
            else:
                if subkey in val:
                    del val[subkey]
            return self.setValue(key=key,value=json.dumps(val),subkey=None,overwrite=overwrite)
        keyhash=_hash_of_key(key)
        db_path=self._get_db_path_for_keyhash(keyhash)
        db = _db_load(db_path)
        doc=db.get(keyhash,None)
        if doc is None:
            doc=dict()
        if value is not None:
            doc['value']=value
            db[keyhash]=doc
        else:
            if keyhash in db:
                del db[keyhash]
        _db_save(db_path,db)
        return True

    def getSubKeys(self,*,key):
        val=self.getValue(key=key,subkey=None)
        try:
            val=json.loads(val)
            return val.keys()
        except:
            return []

    def realizeFile(self,*,path):
        if path.startswith('sha1://'):
            list0=path.split('/')
            sha1=list0[2]
            return self._realize_file_from_sha1(sha1=sha1);
        elif path.startswith('kbucket://'):
            sha1, size, url = self._get_kbucket_file_info(path=path)
            if sha1 is None:
                return None
            try_local_path=self._sha1_cache.findFile(sha1)
            if try_local_path is not None:
                return try_local_path
            return self._sha1_cache.downloadFile(url=url,sha1=sha1,size=size)

        # If the file exists on the local computer, just use that
        if os.path.exists(path):
            return path

        return None

    def saveFile(self,*,path,basename):
        if basename is None:
            basename = os.path.basename(path)

        path0 = path
        path = self.realizeFile(path=path0)
        if not path:
            raise Exception('Unable to realize file in saveFile: '+path0)

        _, sha1 = self._sha1_cache.copyFileToCache(path)

        if sha1 is None:
            raise Exception('Unable to copy file to cache in saveFile: '+path0)

        ret_path = 'sha1://{}/{}'.format(sha1, basename)
        return ret_path

    def _get_db_path_for_keyhash(self,keyhash):
        return self._local_database_path+'/{}/{}.db'.format(keyhash[0],keyhash[1:3])

    def _realize_file_from_sha1(self,*,sha1):
        fname=self._sha1_cache.findFile(sha1)
        if fname is not None:
            return fname
        return None # For now, we don't search kbucket

    def _get_node_info(self, *, share_id):
        if share_id in self._nodeinfo_cache:
            return self._nodeinfo_cache[share_id]
        url = self._kbucket_url+'/'+share_id+'/api/nodeinfo'
        obj = _http_get_json(url)
        if not 'info' in obj:
            return None
        ret=obj['info']
        if ret:
            self._nodeinfo_cache[share_id] = ret
        return ret

    def _get_kbucket_url_for_share(self,*,share_id):
        node_info=self._get_node_info(share_id=share_id)
        if not node_info:
            print('Warning: unable to find node info for share {}'.format(share_id))
            return self._kbucket_url
        if 'accessible' not in node_info:
            url00=node_info.get('listen_url','')+'/'+share_id+'/api/nodeinfo'
            print('Testing whether share {} is directly accessible...'.format(share_id))
            node_info['accessible']=_test_url_accessible(url00,timeout=2)
            if node_info['accessible']:
                print('Share {} is directly accessible.'.format(share_id))
            else:
                print('Share {} is not directly accessible.'.format(share_id))
        if node_info['accessible']:
            return node_info.get('listen_url',None)
        else:
            return self._kbucket_url # TODO: check the parent hub, etc before jumping right to the top


    def _get_kbucket_file_info(self,*,path):
        list0 = path.split('/')
        kbshare_id = list0[2]
        path0 = '/'.join(list0[3:])

        kbucket_url=self._get_kbucket_url_for_share(share_id=kbshare_id)
        if not kbucket_url:
            return (None,None,None)

        url_prv = kbucket_url+'/'+kbshare_id+'/prv/'+path0
        try:
            prv = _http_get_json(url_prv)
        except:
            return (None,None,None)

        if prv is None:
            return (None,None,None)
        try:
            sha1=prv['original_checksum']
            size=prv['original_size']
        except:
            return (None,None,None)
        if not sha1:
            return (None,None,None)

        url_download=kbucket_url+'/'+kbshare_id+'/download/'+path0
        return (sha1,size,url_download)
    

def _http_get_json(url, verbose=False):
    if verbose:
        print('_http_get_json::: '+url)
    try:
        req = request.urlopen(url)
    except:
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
        subdir=ret+'/'+hex(n)[2:]
        if not os.path.exists(subdir):
            os.mkdir(subdir)
    return ret

def _hash_of_key(key):
    if type(key) == dict:
        key = json.dumps(key, sort_keys=True, separators=(',', ':'))
    return _sha1_of_string(key)

def _sha1_of_string(txt):
    hh = hashlib.sha1(txt.encode('utf-8'))
    ret = hh.hexdigest()
    return ret
    

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

# The global module client
client = CairioClient()
