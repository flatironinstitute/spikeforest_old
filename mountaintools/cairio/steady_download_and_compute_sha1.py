import string
import random
import hashlib
import os
import requests


def steady_download_and_compute_sha1(url, target_path, chunk_size=1024*1024*10):
    response = requests.head(url)
    size_bytes = int(response.headers['content-length'])
    str = ''.join(random.sample(string.ascii_lowercase, 8))
    path_tmp = target_path+'.tmp.'+str
    try:
        hh = hashlib.sha1()
        with open(path_tmp, 'wb') as f:
            for ii in range(0, size_bytes, chunk_size):
                jj = ii+chunk_size
                if jj > size_bytes:
                    jj = size_bytes
                headers = {
                    'Range': 'bytes={}-{}'.format(ii, jj-1)
                }
                response = requests.get(url, headers=headers, stream=True)
                for chunk in response.iter_content(chunk_size=5120):
                    if chunk:  # filter out keep-alive new chunks
                        hh.update(chunk)
                        f.write(chunk)
        os.rename(path_tmp, target_path)
        sha1 = hh.hexdigest()
        return sha1
    except:
        if os.path.exists(path_tmp):
            os.remove(path_tmp)
        raise
