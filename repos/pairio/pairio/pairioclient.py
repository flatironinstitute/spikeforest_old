import json
import urllib
import hashlib
import os
import pathlib
import random
import fasteners
import base64

class PairioClient():
    def __init__(self):
        self._config=dict(
            user='', # logged in user for setting remote pairs
            token='', # token for logged in user
            collections=[], # default remote collections to search for get()
            url=os.getenv('PAIRIO_URL','https://pairio.org:10443'), # where the remote collections live
            local_database_path=os.getenv('PAIRIO_DATABASE_DIR',_get_default_local_db_fname()), # for local pairs
            read_local=True, # whether to get locally by default
            write_local=True, # whether to set locally by default
            read_remote=True, # whether to get remotely by default if collections has been set
            write_remote=True # whether to set remotely by default if user/token has been set
        )
        self._verbose=False
    
    def setConfig(self,*,
                  user=None,
                  token=None,
                  collections=None,
                  url=None,
                  local_database_path=None,
                  read_local=None,
                  write_local=None,
                  read_remote=None,
                  write_remote=None,
                  verbose=None
                 ):
        if user:
            if token is None:
                raise Exception('Cannot set user without token.')
            self._config['user']=user
        if token is not None:
            self._config['token']=token
        if collections is not None:
            if type(collections)!=list:
                raise Exception('collections must be a list')
            self._config['collections']=collections
        if url is not None:
            self._config['url']=url
        if local_database_path is not None:
            self._config['local_database_path']=local_database_path
        if read_local is not None:
            self._config['read_local']=read_local
        if write_local is not None:
            self._config['write_local']=write_local
        if read_remote is not None:
            self._config['read_remote']=read_remote
        if write_remote is not None:
            self._config['write_remote']=write_remote
        if verbose is not None:
            self._verbose=verbose

        if user:
            test_key='test.key.'+_random_string(6)
            test_val='test.val.'+_random_string(6)
            try:
                if not self.setRemote(test_key,test_val):
                    raise Exception('Error setting key to remote pairio database.')
            except:
                raise Exception('Error writing to remote pairio database.')

            str2=self.getRemote(test_key,collection=user)

            if str2!=test_val:
                self.setRemote(test_key,None)
                raise Exception('pairio test failed for user={}. {}<>{}'.format(user,str2,test_val))
            else:
                self.setRemote(test_key,None)
                print ('Pairio user set to {}. Test succeeded.'.format(user))

    def getConfig(self):
        ret=self._config.copy()
        if ret['token']:
            ret['token']=None
        return ret

    def get(
        self,
        key,
        collection=None,
        local=None,
        remote=None,
        collections=None,
        return_collection=False
    ):
        url=self._config['url']
        if local is None:
            local=self._config['read_local']
        if remote is None:
            remote=self._config['read_remote']
        if collections is None:
            collections=self._config['collections']
        if collection is not None:
            remote=True
            
        key=_filter_key(key)
        if local and (collection is None):
            val=self._get_local(key)
            if val:
                if not return_collection:
                    return val
                else:
                    return (val,'[local]')
            
        if remote:
            if collection is not None:
                all_collections=[collection]
            else:
                all_collections=collections
            for collection0 in all_collections:
                path='/get/{}/{}'.format(collection0,key)
                url0=url+path
                obj=self._http_get_json(url0)
                if obj['success']:
                    if not return_collection:
                        return obj['value']
                    else:
                        return (obj['value'],collection0)

        if not return_collection:
            return None
        else:
            return (None,None)

    def getLocal(self,key,return_collection=None):
        if not self._config['local_database_path']:
            raise Exception('Cannot read from local database because local_database_path has not been set')
        return self.get(key=key,local=True,remote=False,return_collection=None)

    def getRemote(self,key,*,collection=None):
        if not self._config['user']:
            raise Exception('Cannot read from remote database because user has not been set')
        return self.get(key=key,collection=collection,local=False,remote=True)

    def set(
        self,
        key,
        value,
        local=None,
        remote=None,
        user=None,
        token=None,
        overwrite=None # default is True
    ):
        url=self._config['url']
        if user is None:
            user=self._config['user']
        if token is None:
            token=self._config['token']
        if local is None:
            local=self._config['write_local']
        if remote is None:
            remote=self._config['write_remote']
        if user is None:
            user=self._config['user']
        if token is None:
            token=self._config['token']
        if overwrite is None:
            overwrite=True
        
        key=_filter_key(key)
        if local:
            if not self._set_local(key,value,overwrite=overwrite):
                return False
            
        if remote and user:
            if not url:
                raise Exception('Cannot set value to remote because no url has been set')
            if not token:
                raise Exception('Cannot set value to remote because pairio token has not been set')
            if value:
                path='/set/{}/{}/{}'.format(user,key,value)
            else:
                path='/remove/{}/{}'.format(user,key)
            url0=url+path
            signature=_sha1_of_object({'path':path,'token':token})
            url0=url0+'?signature={}'.format(signature)
            if overwrite is False:
                url0=url0+'&overwrite=false'
            obj=self._http_get_json(url0)
            if not obj['success']:
                print('WARNING: '+obj['error'])
                return False

        return True

    def getObject(
        self,
        key,
        collection=None,
        local=None,
        remote=None,
        collections=None
    ):
        val=self.get(key=key,collection=collection,local=local,remote=remote,collections=collections)
        if not val:
            return val
        val2=json.loads(base64.b64decode(val))
        return val2


    def setObject(
        self,
        key,
        value,
        local=None,
        remote=None,
        user=None,
        token=None,
        overwrite=None # default is True
    ):
        value2=base64.b64encode(json.dumps(value).encode('utf-8')).decode()
        return self.set(key=key,value=value2,local=local,remote=remote,user=user,token=token,overwrite=overwrite)
    
    def setLocal(self,key,value,overwrite=None):
        if not self._config['local_database_path']:
            raise Exception('Cannot write to local database because local_database_path has not been set')
        return self.set(key=key,value=value,user='',local=True,remote=False,overwrite=overwrite)

    def setRemote(self,key,value,overwrite=None):
        if not self._config['user']:
            raise Exception('Cannot write to remote database because user has not been set')
        return self.set(key=key,value=value,local=False,remote=True,overwrite=overwrite)

    def _get_local(self,key):
        local_database_path=self._config['local_database_path']
        if not local_database_path:
            raise Exception('Cannot read from local database because local_database_path has not been set')
        hashed_key=_sha1_of_string(key)
        path=local_database_path+'/{}.db'.format(hashed_key[0:2])
        db = _db_load(path)
        doc=db.get(key,None)
        if doc:
            return doc['value']
        else:
            return None
        
    def _set_local(self,key,val,overwrite=None):
        if overwrite is None:
            overwrite=True
        local_database_path=self._config['local_database_path']
        if not local_database_path:
            raise Exception('Cannot write to local database because local_database_path has not been set')
        hashed_key=_sha1_of_string(key)
        path=local_database_path+'/{}.db'.format(hashed_key[0:2])
        with fasteners.InterProcessLock(path+'.lockfile'):
            db = _db_load(path)
            if overwrite is False:
                if key in db:
                    return False
            if val:
                doc=dict(value=val)
                db[key]=doc;
            else:
                if key in db:
                    del db[key]
            _db_save(path,db)
        return True

    def _http_get_json(self,url):
        return _http_get_json(url,verbose=self._verbose)

def _get_default_local_db_fname():
    dirname=str(pathlib.Path.home())+'/.pairio'
    if not os.path.exists(dirname):
        os.mkdir(dirname)
    ret=dirname+'/database'
    if not os.path.exists(ret):
        os.mkdir(ret)
    return ret

## TODO: make the following thread-safe
def _db_load(path):
    try:
        db=_read_json_file(path)
    except:
        db=dict()
    return db

## TODO: make the following thread-safe
def _db_save(path,db):
    _write_json_file(db,path)

def _read_json_file(path):
  with open(path) as f:
    return json.load(f)

def _write_json_file(obj,path):
  with open(path,'w') as f:
    return json.dump(obj,f)
        
def _filter_key(key):
    if type(key)==str:
        return key
    if type(key)==dict:
        txt=json.dumps(key, sort_keys=True, separators=(',', ':'))
        return _sha1_of_string(txt)
    raise Exception('Invalid type for key')
        
def _http_get_json(url,verbose=False):
    if verbose:
      print ('_http_get_json::: '+url)
    try:
        req=urllib.request.urlopen(url)
    except:
        raise Exception('Unable to open url: '+url)
    try:
        ret=json.load(req)
    except:
        raise Exception('Unable to load json from url: '+url)
    if verbose:
      print ('done.')
    return ret

def _sha1_of_string(txt):
    hh = hashlib.sha1(txt.encode('utf-8'))
    ret=hh.hexdigest()
    return ret

def _sha1_of_object(obj):
    txt=json.dumps(obj, sort_keys=True, separators=(',', ':'))
    return _sha1_of_string(txt)

def _random_string(num_chars):
  chars='abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789'
  return ''.join(random.choice(chars) for _ in range(num_chars))

# The global module client
client=PairioClient()
