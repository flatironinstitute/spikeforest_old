import hashlib
import json
import urllib.request as request
import base64
import os
import requests
import time
import mtlogging
from typing import Union, Dict, List, Optional, Any
from .mttyping import StrOrDict


class MountainRemoteClient():
    def __init__(self):
        pass

    def addCollection(self, *, collection: str, token: str, url: str, admin_token: str) -> bool:
        if not url:
            print('Missing url for remote mountain server.')
            return False
        if not admin_token:
            print('Missing admin token for remote mountain server.')
            return False
        path = '/admin/create/{}/{}'.format(collection, token)
        signature = _sha1_of_object({'path': path, 'token': admin_token})
        url0 = url + path
        url0 = url0 + '?signature={}'.format(signature)
        obj = _http_get_json(url0)
        if not obj.get('success'):
            print('Problem adding collection: ' + obj.get('error', ''))
            return False
        return True

    def getValue(self, *, collection: str, key: StrOrDict, subkey: Optional[str], url: str) -> Optional[str]:
        if not url:
            print('Missing url for remote mountain server.')
            raise ValueError('Missing url for remote mountain server.')
        keyhash = _hash_of_key(key)
        if subkey is None:
            path = '/get/{}/{}'.format(collection, keyhash)
        else:
            path = '/get/{}/{}/{}'.format(collection, keyhash, subkey)
        url0 = url + path
        obj = _http_get_json(url0)
        if not obj.get('success'):
            return None
        return obj['value']

    def setValue(self, *, collection: str, key: StrOrDict, subkey: Optional[str], overwrite: bool=True, value: Optional[str], url: str, token: str) -> bool:
        value_b64: Optional[str] = None
        if value:
            value_b64 = base64.b64encode(value.encode()).decode('utf-8')
        if not url:
            print('Missing url for remote mountain server.')
            raise ValueError('Missing url for remote mountain server.')
        if not token:
            print('Missing token for remote mountain server.')
            raise ValueError('Missing token for remote mountain server.')
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
        url0 = url + path
        url0 = url0 + '?signature={}'.format(signature)
        if not overwrite:
            url0 = url0 + '&overwrite=false'
        obj = _http_get_json(url0)
        if not obj.get('success'):
            if overwrite:
                raise Exception('Problem setting value in collection {}: {}'.format(
                    collection, obj.get('error', '')))
            return False
        return True

    def getSubKeys(self, *, collection: str, key: StrOrDict, url: str) -> List[str]:
        # TODO - fix this - do not require downloading the entire object - will prob require modifying api of server
        val = self.getValue(collection=collection,
                            key=key, url=url, subkey='-')
        if val is None:
            return []
        try:
            valobj = json.loads(val)
            return valobj.keys()
        except:
            return []


def _hash_of_key(key: Union[Dict, List, str]) -> str:
    key_str: str = ""
    if (type(key) == dict) or (type(key) == list):
        key_str = json.dumps(key, sort_keys=True, separators=(',', ':'))
    else:
        key_str = str(key)
        if key_str.startswith('~'):
            return key_str[1:]

    return _sha1_of_string(key_str)


def _sha1_of_string(txt: str) -> str:
    hh = hashlib.sha1(txt.encode('utf-8'))
    ret = hh.hexdigest()
    return ret


def _sha1_of_object(obj: Union[List, Dict]) -> str:
    txt = json.dumps(obj, sort_keys=True, separators=(',', ':'))
    return _sha1_of_string(txt)


@mtlogging.log()
def _http_get_json(url: str, verbose: Optional[bool]=None, retry_delays: Optional[List[float]]=None) -> Optional[str]:
    timer = time.time()
    if retry_delays is None:
        retry_delays = [0.2, 0.5]
    if verbose is None:
        verbose = (os.environ.get('HTTP_VERBOSE', '') == 'TRUE')
    if verbose:
        print('_http_get_json::: ' + url)
    try:
        req = request.urlopen(url)
    except:
        if len(retry_delays) > 0:
            print('Retrying http request in {} sec: {}'.format(
                retry_delays[0], url))
            time.sleep(retry_delays[0])
            return _http_get_json(url, verbose=verbose, retry_delays=retry_delays[1:])
        else:
            raise Exception('Unable to open url: ' + url)
    try:
        ret = json.load(req)
    except:
        raise Exception('Unable to load json from url: ' + url)
    if verbose:
        print('Elapsed time for _http_get_json: {} {}'.format(time.time() - timer, url))
    return ret
