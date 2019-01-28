import urllib
import json
import os
import random
import hashlib
import requests
import random
from pairio import client as pairio
from shutil import copyfile
from .steady_download_and_compute_sha1 import steady_download_and_compute_sha1
from datetime import datetime as dt

class KBucketClient():
  def __init__(self):
    self._config=dict(
        share_ids=[], # remote kbucket shares to search for files
        url=os.getenv('KBUCKET_URL','https://kbucket.flatironinstitute.org'), # the kbucket hub url
        upload_share_id=None,
        upload_token=None,
        local_cache_dir=os.getenv('KBUCKET_CACHE_DIR','/tmp/sha1-cache'),
        load_local=True,
        load_remote=True,
        save_remote=True
    )
    self._sha1_cache=Sha1Cache()
    self._sha1_cache.setDirectory(self._config['local_cache_dir'])
    self._nodeinfo_cache={}
    self._verbose=False

  def setConfig(self,*,
    share_ids=None,
    url=None,
    upload_share_id=None,
    upload_token=None,
    local_cache_dir=None,
    load_local=None,
    load_remote=None, save_remote=None,
    verbose=None
  ):
    if share_ids is not None:
      if type(share_ids)!=list:
        raise Exception('share_ids must be a list')
      self._config['share_ids']=share_ids
    if url is not None:
      self._config['url']=url
    if upload_share_id:
      if not upload_token:
        raise Exception('Cannot set upload_share_id without upload token')
      self._config['upload_share_id']=upload_share_id
    if upload_token is not None:
      self._config['upload_token']=upload_token
    if local_cache_dir is not None:
      self._config['local_cache_dir']=local_cache_dir
      self._sha1_cache.setDirectory(self._config['local_cache_dir'])
    if load_local is not None:
      self._config['load_local']=load_local
    if load_remote is not None:
      self._config['load_remote']=load_remote
    if save_remote is not None:
      self._config['save_remote']=save_remote
    if verbose is not None:
      self._verbose=verbose

  def getConfig(self):
    ret=self._config.copy()
    if ret['upload_token']:
        ret['upload_token']=None
    return ret

  def testSaveRemote(self):
    if not self._config['upload_share_id']:
      raise Exception('Cannot test upload. Share id has not been set.')
    print ('Testing upload to: '+self._config['upload_share_id'])
    try:
      self.saveObject({'test':'upload'},key={'test':'upload'},remote=True)
    except:
      raise Exception('Upload failed.')
    print ('Test upload successful.')

  def findFile(self,path=None,*,sha1=None,share_ids=None,key=None,collection=None,local=None,remote=None):
    path, sha1, size = self._find_file_helper(path=path,sha1=sha1,share_ids=share_ids,key=key,collection=collection,local=local,remote=remote)
    return path

  def realizeFile(self,path=None,*,sha1=None,share_ids=None,target_path=None,key=None,collection=None,local=None,remote=None,verbose=True):
    path, sha1, size = self._find_file_helper(path=path,sha1=sha1,share_ids=share_ids,key=key,collection=collection,local=local,remote=remote)
    if not path:
      return None
    if not _is_url(path):
      if target_path is not None:
        if target_path==path:
          return path
        else:
          copyfile(path,target_path)
          return path
      else:
        return path
    return self._sha1_cache.downloadFile(url=path,sha1=sha1,target_path=target_path,size=size,verbose=verbose)

  def getFileSize(self, path=None,*,sha1=None,share_ids=None,key=None,collection=None,local=None,remote=None):
    path, sha1, size = self._find_file_helper(path=path,sha1=sha1,share_ids=share_ids,key=key,collection=collection,local=local,remote=remote)
    return size

  def moveFileToCache(self,path):
    return self._sha1_cache.moveFileToCache(path)

  def copyFileToCache(self,path):
    return self._sha1_cache.copyFileToCache(path)

  def readDir(self,path,recursive=False,include_sha1=True):
    if path.startswith('kbucket://'):
      list=path.split('/')
      share_id=_filter_share_id(list[2])
      path0='/'.join(list[3:])
      ret=self._read_kbucket_dir(share_id=share_id,path=path0,recursive=recursive,include_sha1=include_sha1)
    else:
      ret=self._read_file_system_dir(path=path,recursive=recursive,include_sha1=include_sha1)
    return ret

  def pairioClient(self):
    return pairio

  def _read_file_system_dir(self,*,path,recursive,include_sha1):
      ret=dict(
        files={},
        dirs={}
      )
      list=_safe_list_dir(path)
      for name0 in list:
        path0=path+'/'+name0
        if os.path.isfile(path0):
          ret['files'][name0]=dict(
            size=os.path.getsize(path0)
          )
          if include_sha1:
            ret['files'][name0]['sha1']=self.computeFileSha1(path0)
        elif os.path.isdir(path0):
          ret['dirs'][name0]={}
          if recursive:
            ret['dirs'][name0]=self._read_file_system_dir(path=path0,recursive=recursive,include_sha1=include_sha1)
      return ret

  def _read_kbucket_dir(self,*,share_id,path,recursive,include_sha1):
    url=self._config['url']+'/'+share_id+'/api/readdir/'+path
    obj=self._http_get_json(url)
    if not obj['success']:
      return None

    ret=dict(
      files={},
      dirs={}
    )
    for file0 in obj['files']:
      name0=file0['name']
      ret['files'][name0]=dict(
        size=file0['size']
      )
      if include_sha1:
        if 'prv' in file0:
          ret['files'][name0]['sha1']=file0['prv']['original_checksum']
    for dir0 in obj['dirs']:
      name0=dir0['name']
      ret['dirs'][name0]={}
      if recursive:
        ret['dirs'][name0]=_read_kbucket_dir(path+'/'+name0)
    return ret

  def computeFileSha1(self,path):
    if path.startswith('sha1://'):
      list=path.split('/')
      sha1=list[2]
      return sha1
    elif path.startswith('kbucket://'):
      path, sha1, size = self._find_file_helper(path=path)
      return sha1
    else:
      return self._sha1_cache.computeFileSha1(path)

  def computeDirHash(self,path):
    dd=self.readDir(path=path,recursive=True,include_sha1=True)
    return _sha1_of_object(dd)

  def _save_file_helper(self,path,share_id=None,upload_token=None,basename=None,remote=None):
    if remote is None:
      remote=self._config['save_remote']
    if not share_id:
      share_id=self._config['upload_share_id']
    if share_id:
      share_id=_filter_share_id(share_id)  

    if basename is None:
      basename=os.path.basename(path)
    
    if not upload_token:
      upload_token=self._config['upload_token']


    if (remote) and (share_id) and (not upload_token):
      raise Exception('Upload token not set for share_id='+share_id)

    path=self.realizeFile(path)
    if not path:
      raise Exception('Unable to realize file for upload.')
    sha1=self.computeFileSha1(path)

    ret_path='sha1://{}/{}'.format(sha1,basename)

    self.copyFileToCache(path)

    if (not remote) or (not share_id):
      # share_id not set... not uploading.
      return ret_path

    url00,size00=self._find_in_share(sha1=sha1,share_id=share_id)
    if url00:
      print ('Already on server.')
      return ret_path

    server_url=self._get_cas_upload_url_for_share(share_id=share_id)

    url_check_path0='/check/'+sha1
    signature=_sha1_of_object({'path':url_check_path0,'token':upload_token})
    url_check=server_url+url_check_path0+'?signature='+signature+'&size={}'.format(os.path.getsize(path))
    resp_obj=self._http_get_json(url_check)
    if not resp_obj['success']:
      raise Exception('Problem checking for upload: '+resp_obj['error'])
    if not resp_obj['okay_to_upload']:
      print ('Cannot upload: '+resp_obj['message'])
      return

    if not resp_obj['found']:
      url_path0='/upload/'+sha1
      signature=_sha1_of_object({'path':url_path0,'token':upload_token})
      url=server_url+url_path0+'?signature='+signature
      resp_obj=_http_post_file_data(url,path)
      if not resp_obj['success']:
        raise Exception('Problem posting file data: '+resp_obj['error'])
    else:
      print ('Already on server (*)')

    return ret_path

  def saveFile(self,fname,*,key=None,share_id=None,upload_token=None,basename=None,remote=None):
    ret=self._save_file_helper(fname,share_id=share_id,upload_token=upload_token,basename=basename,remote=remote)

    if key:
      sha1=self.computeFileSha1(fname)
      pairio.set(key,sha1)

    return ret

  def saveObject(self,object,*,key,format='json',share_id=None,upload_token=None,remote=None):
    tmp_fname=self._create_temporary_file_for_object(object=object,format=format)
    try:
      fname=self.moveFileToCache(tmp_fname)
    except:
      _safe_remove_file(tmp_fname)
      raise
    self.saveFile(fname,share_id=share_id,upload_token=upload_token,key=key,basename='object.json',remote=remote)

  def loadObject(self,*,format='json',share_ids=None,key=None,collection=None,local=None,remote=None):
    fname=self.realizeFile(share_ids=share_ids,key=key,collection=collection,local=local,remote=remote)
    if fname is None:
      raise Exception('Unable to find file.')
    if format=='json':
      ret=_read_json_file(fname)
      if not ret:
        raise Exception('Unable to read or parse json file: '+fname)
    else:
      raise Exception('Unsupported format in loadObject: '+format)
    return ret

  def getTemporaryFileName(self,fname):
    return self._create_temporary_fname(fname)

  def _create_temporary_file_for_object(self,*,object,format):
    tmp_fname=self._create_temporary_fname('object.json')
    if format=='json':
      _write_json_file(object,tmp_fname)
    else:
      raise Exception('Unsupported format in saveObject: '+format)
    return tmp_fname

  def _create_temporary_fname(self,fname):
    return self._config['local_cache_dir']+'/tmp_kucketclient_'+''.join(random.choices('abcdefghijklmnopqrstuvwxyz', k=10))+'.'+fname

  def getNodeInfo(self,share_id):
    if share_id in self._nodeinfo_cache:
      return self._nodeinfo_cache[share_id]
    share_id=_filter_share_id(share_id)
    url=self._config['url']+'/'+share_id+'/api/nodeinfo'
    ret=self._http_get_json(url)
    if ret:
      self._nodeinfo_cache[share_id]=ret
    return ret

  def _find_file_helper(self,*,path,sha1=None,share_ids=None,key=None,collection=None,local=None,remote=None):
    if local is None:
      local=self._config['load_local']
    if remote is None:
      remote=self._config['load_remote']
    if share_ids is None:
      share_ids=self._config['share_ids']
    if key is not None:
      sha1=pairio.get(key=key,collection=collection)
      if not sha1:
        return (None,None,None)
    if path is not None:
      if sha1 is not None:
        raise Exception('Cannot specify both path and sha1 in find file')
      if path.startswith('sha1://'):
        list=path.split('/')
        sha1=list[2]
        ### continue to below
      elif path.startswith('kbucket://'):
        list=path.split('/')
        share_ids=[_filter_share_id(list[2])]
        path0='/'.join(list[3:])
        prv=self._get_prv_for_file(share_id=share_ids[0],path=path0)
        if not prv:
          return (None, None, None)
        sha1=prv['original_checksum']
        remote=True
        ### continue to below
      else:
        if os.path.exists(path) and os.path.isfile(path):
          return (path, None, os.path.getsize(path))
        else:
          return (None, None, None)
  
    # search locally
    if local:
      path=self._sha1_cache.findFile(sha1=sha1)
    else:
      path=''
      
    if path:
      return (path,sha1,os.path.getsize(path))

    if remote:
      for id in share_ids:
        url,size=self._find_in_share(sha1=sha1,share_id=id)
        if url:
          return (url,sha1,size)

    return (None,None,None)

  def _get_prv_for_file(self,*,share_id,path):
    url=self._config['url']+'/'+share_id+'/prv/'+path
    try:
      obj=self._http_get_json(url)
    except:
      return None
    return obj

  def _find_in_share(self,*,sha1,share_id):
    share_id=_filter_share_id(share_id)
    url=self._config['url']+'/'+share_id+'/api/find/'+sha1
    obj=self._http_get_json(url)
    if not obj['success']:
      raise Exception('Error finding file in share: '+obj['error'])
    if not obj['found']:
      return (None,None)
    urls0=obj['urls']
    results0=obj['results']
    for url0 in urls0:
      if _test_url_accessible(url0):
        size0=results0[0]['size']
        return (url0,size0)
    return (None,None)

  def _get_cas_upload_url_for_share(self,share_id):
    node_info=self.getNodeInfo(share_id)
    if not node_info:
      raise Exception('Unable to get node info for share: '+share_id)
    if not 'info' in node_info:
      raise Exception('node_info does not have info field for share: '+share_id)
    if not 'cas_upload_url' in node_info['info']:
      raise Exception('node_info does not have info.cas_upload_url field for share: '+share_id)
    return node_info['info'].get('cas_upload_url',None)

  def _http_get_json(self,url):
    return _http_get_json(url,verbose=self._verbose)

def _http_get_json(url,verbose=False):
    timer=dt.now()
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

def _http_post_file_data(url,fname):
  with open(fname, 'rb') as f:
    try:
      obj=requests.post(url, data=f)
    except:
      raise Exception('Error posting file data.')
  if obj.status_code!=200:
    raise Exception('Error posting file data: {} {}'.format(obj.status_code,obj.content.decode('utf-8')))
  return json.loads(obj.content)

def _test_url_accessible(url):
  try:
    req = urllib.request.Request(url, method="HEAD")
    code=urllib.request.urlopen(req).getcode()
    return (code==200)
  except:
    return False

def _is_url(path):
  return ((path.startswith('http://')) or (path.startswith('https://')))

_filter_share_id_cache={}
def _filter_share_id(id):
  if id in _filter_share_id_cache:
    return _filter_share_id_cache[id]
  if '.' in id:
    list=id.split('.')
    if len(list)!=2:
      return id
    ret=pairio.get(list[1],collection=list[0])
    if ret:
      _filter_share_id_cache[id]=ret
    return ret
  else:
    return id

def _safe_list_dir(path):
  try:
    ret=os.listdir(path)
    return ret
  except:
    print ('Warning: unable to listdir: '+path)
    return []

# TODO: implement cleanup() for Sha1Cache
# removing .record.json and .hints.json files that are no longer relevant
class Sha1Cache():
  def __init__(self):
    self._directory=''
  def setDirectory(self,directory):
    if not os.path.exists(directory):
      os.mkdir(directory)
    self._directory=directory
  def findFile(self,sha1):
    path=self._get_path(sha1,create=False)
    if os.path.exists(path):
      return path
    hints_fname=path+'.hints.json'
    if os.path.exists(hints_fname):
      hints=_read_json_file(hints_fname)
      if hints and ('files' in hints):
        files=hints['files']
        matching_files=[]
        for file in files:
          path0=file['stat']['path']
          if os.path.exists(path0) and os.path.isfile(path0):
            stat_obj0=_get_stat_object(path0)
            if stat_obj0:
              if (_stat_objects_match(stat_obj0,file['stat'])):
                to_return=path0
                matching_files.append(file)
        if len(matching_files)>0:
          hints['files']=matching_files
          try:
            _write_json_file(hints,hints_fname)
          except:
            print ('Warning: problem writing hints file: '+hints_fname)
          return matching_files[0]['stat']['path']
        else:
          _safe_remove_file(hints_fname)
      else:
        print ('Warning: failed to load hints json file, or invalid file. Removing: '+hints_fname)
        _safe_remove_file(hints_fname)

  def downloadFile(self,url,sha1,target_path=None,size=None,verbose=True):
    alternate_target_path=False
    if target_path is None:
      target_path=self._get_path(sha1,create=True)
    else:
      alternate_target_path=True
    path_tmp=target_path+'.downloading'
    size_mb='unknown'
    if size:
      size_mb=int(size/(1024*1024)*10)/10
    if verbose:
      print ('Downloading file --- ({} MB): {} -> {}'.format(size_mb,url,target_path))
    sha1b=steady_download_and_compute_sha1(url=url,target_path=path_tmp)
    if not sha1b:
      if os.path.exists(path_tmp):
        _safe_remove_file(path_tmp)
    if sha1!=sha1b:
      if os.path.exists(path_tmp):
        _safe_remove_file(path_tmp)
      raise Exception('sha1 of downloaded file does not match expected {} {}'.format(url,sha1))
    if os.path.exists(target_path):
      _safe_remove_file(target_path)
    os.rename(path_tmp,target_path)
    if alternate_target_path:
      self.computeFileSha1(target_path,_known_sha1=sha1)
    return target_path

  def moveFileToCache(self,path):
    sha1=self.computeFileSha1(path)
    path0=self._get_path(sha1,create=True)
    if os.path.exists(path0):
      if path!=path0:
        _safe_remove_file(path)
    else:
      os.rename(path,path0)
    return path0

  def copyFileToCache(self,path):
    sha1=self.computeFileSha1(path)
    path0=self._get_path(sha1,create=True)
    if not os.path.exists(path0):
      copyfile(path,path0+'.copying')
      os.rename(path0+'.copying',path0)
    return path0

  def computeFileSha1(self,path,_known_sha1=None):
    aa=_get_stat_object(path)
    aa_hash=_compute_string_sha1(json.dumps(aa, sort_keys=True))

    path0=self._get_path(aa_hash,create=True)+'.record.json'
    if os.path.exists(path0):
      obj=_read_json_file(path0)
      if obj:
        bb=obj['stat']
        if _stat_objects_match(aa,bb):
          if obj.get('sha1',None):
            return obj['sha1']
    if _known_sha1 is None:
      sha1=_compute_file_sha1(path)
    else:
      sha1=_known_sha1

    if not sha1:
      return None

    obj=dict(
      sha1=sha1,
      stat=aa
    )
    try:
      _write_json_file(obj,path0)
    except:
      print ('Warning: problem writing .record.json file: '+path0)

    path1=self._get_path(sha1,create=True,directory=self._directory)+'.hints.json'
    if os.path.exists(path1):
      hints=_read_json_file(path1)
    else:
      hints=None
    if not hints:
      hints={'files':[]}
    hints['files'].append(obj)
    try:
      _write_json_file(hints,path1)
    except:
      print ('Warning: problem writing .hints.json file: '+path1)
    ## todo: use hints for findFile
    return sha1

  def _get_path(self,sha1,*,create=True,directory=None):
    if directory is None:
      directory=self._directory
    path0=directory+'/{}/{}{}'.format(sha1[0],sha1[1],sha1[2])
    if create:
      if not os.path.exists(path0):
        os.makedirs(path0)
    return path0+'/'+sha1
  #def _download_and_compute_sha1(self,url,path):
  #  hh = hashlib.sha1()
  #  response=requests.get(url,stream=True)
  #  path_tmp=path+'.'+_random_string(6)
  #  with open(path_tmp,'wb') as f:
  #    for chunk in response.iter_content(chunk_size=512):
  #      if chunk:  # filter out keep-alive new chunks
  #        hh.update(chunk)
  #        f.write(chunk)
  #  os.rename(path_tmp,path)
  #  return hh.hexdigest()

def _compute_file_sha1(path):
  if (os.path.getsize(path)>1024*1024*100):
    print ('Computing sha1 of {}'.format(path))
  BLOCKSIZE = 65536
  sha = hashlib.sha1()
  with open(path, 'rb') as file:
      buf = file.read(BLOCKSIZE)
      while len(buf) > 0:
          sha.update(buf)
          buf = file.read(BLOCKSIZE)
  return sha.hexdigest()

def _get_stat_object(fname):
  try:
    stat0=os.stat(fname)
    obj=dict(
        path=fname,
        size=stat0.st_size,
        ino=stat0.st_ino,
        mtime=stat0.st_mtime,
        ctime=stat0.st_ctime
    )
    return obj
  except:
    return None

def _stat_objects_match(aa,bb):
  str1=json.dumps(aa, sort_keys=True)
  str2=json.dumps(bb, sort_keys=True)
  return (str1==str2)

def _compute_string_sha1(txt):
  hash_object = hashlib.sha1(txt.encode('utf-8'))
  return hash_object.hexdigest()

def _sha1_of_object(obj):
  txt=json.dumps(obj, sort_keys=True, separators=(',', ':'))
  return _compute_string_sha1(txt)

def _safe_remove_file(fname):
  try:
    os.remove(fname)
  except:
    print ('Warning: unable to remove file that we thought existed: '+fname)

def _read_json_file(path):
  try:
    with open(path) as f:
      return json.load(f)
  except:
    print ('Warning: Unable to read or parse json file: '+path)
    return None

def _write_json_file(obj,path):
  with open(path,'w') as f:
    return json.dump(obj,f)

def _random_string(num_chars):
  chars='abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789'
  return ''.join(random.choice(chars) for _ in range(num_chars))

# The global module client
client=KBucketClient()
