import hashlib
import json
import urllib.request as request
import base64
import os
import requests
import time
import mtlogging

class MountainRemoteClient():
    def __init__(self):
        pass

    def addCollection(self, *, collection, token, url, admin_token):
        if not url:
            print('Missing url for remote mountain server.')
            return False
        if not admin_token:
            print('Missing admin token for remote mountain server.')
            return False
        path = '/admin/create/{}/{}'.format(collection, token)
        signature = _sha1_of_object({'path': path, 'token': admin_token})
        url0 = url+path
        url0 = url0+'?signature={}'.format(signature)
        obj = _http_get_json(url0)
        if not obj.get('success'):
            print('Problem adding collection: '+obj.get('error', ''))
            return False
        return True

    def getValue(self, *, collection, key, subkey, url):
        if not url:
            print('Missing url for remote mountain server.')
            return False
        keyhash = _hash_of_key(key)
        if subkey is None:
            path = '/get/{}/{}'.format(collection, keyhash)
        else:
            path = '/get/{}/{}/{}'.format(collection, keyhash, subkey)
        url0 = url+path
        obj = _http_get_json(url0)
        if not obj.get('success'):
            return None
        return obj['value']

    def setValue(self, *, collection, key, subkey, overwrite=True, value, url, token):
        if value:
            value_b64 = base64.b64encode(value.encode()).decode('utf-8')
        if not url:
            print('Missing url for remote mountain server.')
            return False
        if not token:
            print('Missing token for remote mountain server.')
            return False
        keyhash = _hash_of_key(key)
        if value:
            if subkey is None:
                path = '/set/{}/{}/{}'.format(collection, keyhash, value_b64)
            else:
                path = '/set/{}/{}/{}/{}'.format(collection,
                                                 keyhash, subkey, value_b64)
        else:
            if subkey is None:
                path = '/remove/{}/{}'.format(collection, keyhash)
            else:
                path = '/remove/{}/{}/{}'.format(collection, keyhash, subkey)
        signature = _sha1_of_object({'path': path, 'token': token})
        url0 = url+path
        url0 = url0+'?signature={}'.format(signature)
        if not overwrite:
            url0 = url0+'&overwrite=false'
        obj = _http_get_json(url0)
        if not obj.get('success'):
            if overwrite:
                raise Exception('Problem setting value in collection {}: {}'.format(
                    collection, obj.get('error', '')))
            return False
        return True

    def uploadFile(self, *, path, sha1, cas_upload_server_url, upload_token):
        url_check_path0 = '/check/'+sha1
        signature = _sha1_of_object(
            {'path': url_check_path0, 'token': upload_token})
        url_check = cas_upload_server_url+url_check_path0+'?signature=' + \
            signature+'&size={}'.format(os.path.getsize(path))
        resp_obj = _http_get_json(url_check)
        if not resp_obj['success']:
            print('Warning: Problem checking for upload: '+resp_obj['error'])
            return False
        if not resp_obj['okay_to_upload']:
            print('Cannot upload {}: {}'.format(path, resp_obj['message']))
            return False

        if not resp_obj['found']:
            url_path0 = '/upload/'+sha1
            signature = _sha1_of_object(
                {'path': url_path0, 'token': upload_token})
            url = cas_upload_server_url+url_path0+'?signature='+signature
            size0 = os.path.getsize(path)
            if size0 > 10000:
                print(
                    'Uploading file --- ({}): {} -> {}'.format(_format_file_size(size0), path, url))

            timer=time.time()
            resp_obj = _http_post_file_data(url, path)
            elapsed=time.time()-timer

            if size0 > 10000:
                print('File uploaded ({}) in {} sec'.format(_format_file_size(size0), elapsed))
            
            if not resp_obj.get('success', False):
                print('Problem posting file data: '+resp_obj.get('error', ''))
                return False
            return True
        else:
            print('Already on server (**)')
            return True

    def getSubKeys(self, *, collection, key, url):
        # TODO - fix this - do not require downloading the entire object - will prob require modifying api of server
        val = self.getValue(collection=collection,
                            key=key, url=url, subkey='-')
        if val is None:
            return []
        try:
            val = json.loads(val)
            return val.keys()
        except:
            return []


def _hash_of_key(key):
    if type(key) == dict:
        key = json.dumps(key, sort_keys=True, separators=(',', ':'))
    return _sha1_of_string(key)


def _sha1_of_string(txt):
    hh = hashlib.sha1(txt.encode('utf-8'))
    ret = hh.hexdigest()
    return ret


def _sha1_of_object(obj):
    txt = json.dumps(obj, sort_keys=True, separators=(',', ':'))
    return _sha1_of_string(txt)


@mtlogging.log()
def _http_get_json(url, verbose=None, retry_delays=None):
    if retry_delays is None:
        retry_delays = [0.2, 0.5]
    if verbose is None:
        timer = time.time()
        verbose = (os.environ.get('HTTP_VERBOSE', '') == 'TRUE')
    if verbose:
        print('_http_get_json::: '+url)
    try:
        req = request.urlopen(url)
    except:
        if len(retry_delays) > 0:
            print('Retrying http request in {} sec: {}'.format(
                retry_delays[0], url))
            time.sleep(retry_delays[0])
            return _http_get_json(url, verbose=verbose, retry_delays=retry_delays[1:])
        else:
            raise Exception('Unable to open url: '+url)
    try:
        ret = json.load(req)
    except:
        raise Exception('Unable to load json from url: '+url)
    if verbose:
        print('Elapsed time for _http_get_json: {} {}'.format(time.time()-timer, url))
    return ret

@mtlogging.log()
def _http_post_file_data(url, fname, verbose=None):
    if verbose is None:
        timer = time.time()
        verbose = (os.environ.get('HTTP_VERBOSE', '') == 'TRUE')
    if verbose:
        print('_http_post_file_data::: '+fname)
    with open(fname, 'rb') as f:
        try:
            obj = requests.post(url, data=f)
        except:
            raise Exception('Error posting file data.')
    if obj.status_code != 200:
        raise Exception('Error posting file data: {} {}'.format(
            obj.status_code, obj.content.decode('utf-8')))
    if verbose:
        print('Elapsed time for _http_post_file_Data: {}'.format(time.time()-timer))
    return json.loads(obj.content)

# thanks: https://stackoverflow.com/questions/1094841/reusable-library-to-get-human-readable-version-of-file-size


def _format_file_size(size):
    if not size:
        return 'Unknown'
    if size <= 1024:
        return '{} B'.format(size)
    return _sizeof_fmt(size)


def _sizeof_fmt(num, suffix='B'):
    for unit in ['', 'Ki', 'Mi', 'Gi', 'Ti', 'Pi', 'Ei', 'Zi']:
        if abs(num) < 1024.0:
            return "%3.1f %s%s" % (num, unit, suffix)
        num /= 1024.0
    return "%.1f %s%s" % (num, 'Yi', suffix)
