import pathlib
import pickledb
import urllib
import os

class PairioClient():
    def __init__(self):
        self._pairio_user=os.getenv('PAIRIO_USER')
        self._pairio_token=os.getenv('PAIRIO_TOKEN')
        self._pairio_url=os.getenv('PAIRIO_URL')
        self._local_db_path=self._get_local_db_fname()
        if not self._pairio_url:
            self._pairio_url='http://localhost:25340'
    def get(self,key):
        url=self._pairio_url+'/get/{}'.format(key)
        obj=self._http_get_json(url)
        docs=obj['documents']
        return docs
    def getLocal(self,key):
        db = pickledb.load(self._local_db_path, False)
        doc=db.get(key)
        if doc:
            return doc['value']
        else:
            return None
    def setLocal(self,key,val):
        db = pickledb.load(self._local_db_path, False)
        doc=dict(value=val)
        db.set(key,doc)
        db.dump()
    def _get_local_db_fname(self):
        dirname=str(pathlib.Path.home())+'/.pairio'
        if not os.path.exists(dirname):
            os.mkdir(dirname)
        return dirname+'/pairio_local_python.db'
    def _http_get_json(self,url):
        return json.load(urllib.request.urlopen(url))

def getLocal(key):
    PC=PairioClient()
    return PC.getLocal(key)

def setLocal(key,val):
    PC=PairioClient()
    return PC.setLocal(key,val)