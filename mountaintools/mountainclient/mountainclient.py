import json
import urllib.request as request
import hashlib
import os
import sys
import pathlib
import random
import base64
import tempfile
from copy import deepcopy
from datetime import datetime as dt
from .sha1cache import Sha1Cache
from .mountainremoteclient import MountainRemoteClient, _format_file_size, _http_post_file_data
from .mountainremoteclient import _http_get_json
import time
from getpass import getpass
import shutil
from .filelock import FileLock
import mtlogging

env_path=os.path.join(os.environ.get('HOME',''),'.mountaintools', '.env')
if os.path.exists(env_path):
    try:
        from dotenv import load_dotenv
    except:
        raise Exception('Unable to import dotenv. Use pip install python-dotenv')
    load_dotenv(dotenv_path=env_path,verbose=True)

_global_kbucket_mem_sha1_cache = dict()
_global_kbucket_mem_dir_hash_cache = dict()
class MountainClient():
    """
    MountainClient is a python client for accessing local and remote mountain
    databases and KBucket shares. All I/O for MountainTools is handled using
    this client.

    There is a global client that may be imported via

    .. code-block:: python

        from mountaintools import client as mt

    Or you can instantiate a local client object:

    .. code-block:: python

        from mountaintools import MountainClient
        mt_client = MountainClient()

    The global client allows a single login to apply to the entire program, but
    there are also times when using a local instance is preferred.

    By default the client utilizes cache directories on your local disk, but it
    can also be configured to read and write from remote servers. For example,
    the following code saves and retrieves some short text strings using the
    local file system as storage.

    .. code-block:: python

        from mountaintools import client as mt

        # Setting values (these should be short strings, <=80 characters)
        mt.setValue(key='some-key1', value='hello 1')
        mt.setValue(key=dict(name='some_name', number=2), value='hello 2')

        # Getting values
        val1 = mt.getValue(key='some-key1')
        val2 = mt.getValue(key=dict(name='some_name', number=2))

    By default these are stored inside the ~/.mountain database directory. This
    may be configured using the MOUNTAIN_DIR environment variable.

    While setValue() and getValue() are limited to working with short strings,
    larger objects may be stored using saveText(), saveObject() and saveFile(),
    and retrieved using loadText(), loadObject() and loadFile(), as follows:

    .. code-block:: python

        from mountaintools import client as mt

        # Local storage of data and files, retrievable by SHA-1 hash
        some_text = 'This is some text'
        path = mt.saveText(some_text, basename='test.txt')
        print(path)
        # Output: sha1://482cb0cfcbed6740a2bcb659c9ccc22a4d27b369/test.txt

        # Later we can use this to retrieve the text
        retrieved_text = mt.loadText(path=path)

        # ... or retrieve the path to a local file containing the text
        fname = mt.realizeFile(path)
        print(fname)
        # Output: /tmp/sha1-cache/4/82/482cb0cfcbed6740a2bcb659c9ccc22a4d27b369

        # Or we can store some large text by key and retrieve it later
        large_text = 'some large repeating text'*100
        mt.saveText(key=dict(name='key-for-repeating-text'), text=large_text)
        txt = mt.loadText(key=dict(name='key-for-repeating-text'))

        # Similarly we can store python dicts via json content
        some_object = dict(some='object')
        path = mt.saveObject(some_object, basename='object.json')
        print(path)
        # Output: sha1://b77fdda467b03d7a0c3e06f6f441f689ac46e817/object.json

        retrieved_object = mt.loadObject(path=path)
        print(retrieved_object)
        assert json.dumps(retrieved_object) == json.dumps(some_object)

        # Or store objects by key
        some_other_object = dict(some_other='object')
        mt.saveObject(object=some_other_object, key=dict(some='key'))
        obj = mt.loadObject(key=dict(some='key'))
        assert json.dumps(some_other_object) == json.dumps(obj)

        # You can do the same with files
        with open(tempfile.gettempdir()+'/test___.txt', 'w') as f:
            f.write('some file content')
        path = mt.saveFile(tempfile.gettempdir()+'/test___.txt')
        print(path)
        # Output: sha1://ee025361a15e3e8074e9c0b44b4f98aabc829b3d/test___.txt

        # Then load the text of the file at a later time
        txt = mt.loadText(path=path)
        assert txt == 'some file content'

        sha1 = mt.computeFileSha1(path=mt.realizeFile(path))
        txt2 = mt.loadText(path='sha1://'+sha1)
        assert txt2 == 'some file content'

    The larger content is stored in a disk-backed content-addressable storage
    database, located by default at /tmp/sha1-cache. This may be configured by
    setting the KBUCKET_CACHE_DIR environment variable.

    To access content on a remote server, you can use

    .. code-block:: python
        
        from mountaintools import client as mt

        mt.configRemoteReadonly(collection='<collection>', share_id='<id>')

    where <collection> and <id> refer to a remote mountain collection and
    KBucket share ID. For read/write access you will need to either provide
    the authorization tokens or log in as follows:

    .. code-block:: python
        
        from mountaintools import client as mt

        mt.login()
        mt.configRemoteReadWrite(collection='<collection>', share_id='<id>')

    """


    def __init__(self):
        self._pairio_url = os.environ.get(
            'MOUNTAIN_URL', os.environ.get('PAIRIO_URL', os.environ.get('CAIRIO_URL', 'https://pairio.org:20443')))
        self._kachery_urls = dict()
        self._kachery_upload_tokens = dict()
        self._pairio_tokens = dict()
        self._verbose = False
        self._remote_client = MountainRemoteClient()
        self._values_by_alias = dict()
        self._config_download_from = []
        self._local_db = MountainClientLocal(parent=self)
        self._initialize_kacheries()
        self._read_pairio_tokens()

    def autoConfig(self, *, collection, key, ask_password=False, password=None):
        """
        Deprecated
        """
        print('WARNING: autoConfig() is deprecated and will no longer have any effect.')

    def login(self, *, user=None, password=None, interactive=False, ask_password=False):
        '''
        Log in to the mountain system. This acquires a collection of tokens that
        are used by the configRemoteReadWrite() function in order to gain
        read/write access to collections and kbucket shares. The default user
        name and/or password may be set by setting the following variables in
        ~/.mountaintools/.env: MOUNTAIN_USER and MOUNTAIN_PASSWORD.

        The system will prompt for the user name in either of the following
        situations:
        1) No user is specified and MOUNTAIN_USER is not set and
           interactive=True
        2) User is set to '' (empty string) and interactive=True

        The system will prompt for the password in the following situation:
        No password is provided and MOUNTAIN_PASSWORD is not set and
            (interactive = True or ask_password=True)

        Parameters
        ----------
        user: str
            Name of the user
        password: str
            Password of the user
        interactive: bool
            Whether to interactively ask for user/password (see above)
        ask_password: bool
            Whether to ask for the password (see above)
        '''
        if interactive:
            ask_password=True

        try:
            from simplecrypt import encrypt, decrypt
        except:
            raise Exception('Cannot import simplecrypt. Use pip install simple-crypt.')

        if user is None:
            user=os.environ.get('MOUNTAIN_USER','')
            if user and (password is None):
                password=os.environ.get('MOUNTAIN_PASSWORD','')

        if not user:
            if interactive:
                user=input('Mountain user: ')

        if not user:
            raise Exception('Cannot login, no user found. You can store MOUNTAIN_USER and MOUNTAIN_PASSWORD variables in ~/.mountaintools/.env.')

        if not password:
            if ask_password:
                password=getpass('Mountain password for {}: '.format(user))

        if not password:
            raise Exception('Cannot login, no password found. You can store MOUNTAIN_USER and MOUNTAIN_PASSWORD variables in ~/.mountaintools/.env.')

        key=dict(
            name='user_config',
            user=user
        )
        print('Logging in as {}...'.format(user))
        val=self.getValue(
            collection='admin',
            key=key
        )
        if not val:
            raise Exception('Unable to find config for user: {}'.format(user))
        config=json.loads(
            decrypt(
                password,
                base64.b64decode(val.encode('utf-8'))
            )
        )
        if 'pairio_tokens' in config:
            for key0, val0 in config['pairio_tokens'].items():
                self.setPairioToken(key0, val0)
        if 'kachery_upload_tokens' in config:
            for key0, val0 in config['kachery_upload_tokens'].items():
                self.setKacheryUploadToken(key0, val0)
        print('Logged in as {}'.format(user))

    def setPairioToken(self, collection, token):
        self._pairio_tokens[collection] = token

    def setKacheryUploadToken(self, kachery_name, token):
        self._kachery_upload_tokens[kachery_name] = token

    def configLocal(self):
        """
        Deprecated
        """
        print('WARNING: configLocal() is deprecated and will no longer have any effect.')
    
    def configRemoteReadonly(self, *, collection=None, share_id='', alternate_share_ids=[]):
        """
        Deprecated
        """
        print('WARNING: configRemoteReadonly() is deprecated and will no longer have any effect.')

    def configRemoteReadWrite(self, *, collection=None, share_id, token=None, upload_token=None):
        """
        Deprecated
        """
        print('WARNING: configRemoteReadWrite() is deprecated and will no longer have any effect.')

    def setRemoteConfig(self, *, url=0, collection=0, token=0, share_id=0, upload_token=0, alternate_share_ids=0):
        """
        Deprecated
        """
        print('WARNING: setRemoteConfig() is deprecated and will no longer have any effect.')

    def getRemoteConfig(self):
        """
        Deprecated
        """
        print('WARNING: getRemoteConfig() is deprecated and only returns an empty dict.')
        return dict()

    def addRemoteCollection(self, collection, token, admin_token):
        """
        Add a remote collection, or set the token for an existing collection
        (requires admin access).
        
        Parameters
        ----------
        collection : str
            Name of the remote collection.
        token : str
            The new token.
        admin_token : str
            The admin token for the mountain server
        
        Returns
        -------
        bool
            True if successful.
        """
        return self._remote_client.addCollection(
            collection=collection,
            token=token,
            url=self._pairio_url,
            admin_token=admin_token
        )

    def configDownloadFrom(self, kachery_names):
        if type(kachery_names) == str:
            kachery_names=[kachery_names]
        for kname in kachery_names:
            if kname not in self._config_download_from:
                self._config_download_from.append(kname)
    
    def getDownloadFromConfig(self):
        return deepcopy(dict(
            download_from=self._config_download_from
        ))

    def setDownloadFromConfig(self, obj):
        self._config_download_from = obj.get('download_from', [])

    @mtlogging.log(name='MountainClient:getValue')
    def getValue(self, *, key, subkey=None, parse_json=False, collection=None, local_first=False, check_alt=False):
        """
        Retrieve a string value from the local database or, if connected to a
        remote mountain collection, from a remote database. This is used to
        retrieve relatively small strings (generally fewer than 80 characters)
        that were previously associated with keys via setValue(). The keys can
        either be strings or python dicts. In addition to keys, subkeys may also
        be provided. To retrieve larger text strings, objects, or files, use
        loadText(), loadObject(), or realizeFile() instead.
        
        Parameters
        ----------
        key : str or dict
            The key used to look up the value
        subkey : str, optional
            A subkey string (the default is None, which means that no subkey is
            used). To retrieve values for all subkeys, use subkey='-'. In that
            case a JSON string is returned containing all the values -- you may
            want to set parse_json=True in this case to return a dict.
        parse_json : bool, optional
            Whether to parse the string value as JSON and return a dict (the
            default is False)
        collection : str, optional
            The name of the collection to retrieve the value from, which may be
            different from the collection specified in configRemoteReadonly()
            configRemoteReadWrite() (the default is None, which means that the
            configured collection is used)
        local_first : bool, optional
            Whether to search the local database prior to searching any remote
            collections (the default is False)
        
        Returns
        -------
        str or None
            The string if found in the database. Otherwise returns None.
        """
        ret = self._get_value(key=key, subkey=subkey,
                              collection=collection, local_first=local_first, check_alt=check_alt)
        if parse_json and ret:
            try:
                ret = json.loads(ret)
            except:
                print('Warning: Problem parsing json in MountainClient.getValue()')

                return None
        return ret

    @mtlogging.log(name='MountainClient:setValue')
    def setValue(self, *, key, subkey=None, value, overwrite=True, local_also=False, collection=None):
        """
        Store a string value to the local database or, if connected to a remote
        mountain collection, to a remote database. This is used to store
        relatively small strings (generally fewer than 80 characters) and
        associate them with keys for subsequent retrieval using getValue(). The
        keys can either be strings or python dicts. In addition to keys, subkeys
        may also be provided. To store larger text strings, objects, or files,
        use saveText(), saveObject(), or saveFile() instead.
        
        Parameters
        ----------
        key : str or dict
            The key used for future lookups via getValue()
        value : str
            The string value to store (usually fewer than 80 characters). If
            value=None then the key is removed from the database.
        subkey : str, optional
            The optional subkey for storing the value. If sukey='-' and value is
            None, then all the subkeys are removed from the database. (The
            default is None, which means that no subkey is used)
        overwrite : bool, optional
            Whether to overwrite an existing entry. If False, then the function
            will be successful only if no value was previously set. (The default
            is True)
        local_also : bool, optional
            Whether to also store the value in the local base. This applies when
            the client is configured to write to a remote collection. (The
            default is False)
        
        Returns
        -------
        bool
            True if successful
        """
        return self._set_value(key=key, subkey=subkey, value=value, overwrite=overwrite, local_also=local_also, collection=collection)

    @mtlogging.log(name='MountainClient:getSubKeys')
    def getSubKeys(self, key, collection=None):
        """
        Retrieve the list of subkeys associated with a key
        
        Parameters
        ----------
        key : str or dict
            The used by setValue(), saveText(), saveObject(), or saveFile()
        
        Returns
        -------
        list of str
            The list of subkeys
        """
        return list(self._get_sub_keys(key=key, collection=collection))

    @mtlogging.log(name='MountainClient:realizeFile')
    def realizeFile(self, path=None, *, key=None, subkey=None, dest_path=None, local_first=False, show_progress=False, collection=None, download_from=None):
        """
        Return a local path to the specified file, downloading the file from a
        remote server to the local SHA-1 cache if needed. In other words,
        "realize" the file on the local file system. There are four ways to
        refer to a file:

        1) By local path. For example, path = '/path/to/local/file.dat'
        2) By SHA-1 URL. For example, path =
           'sha1://7bf5432e9266831ab7d64d193fe3f8c69c9e04cc/experiment1/raw.dat'
        3) By kbucket URL. For example, path =
           'kbucket://59317022c908/experiment1/raw.dat'
        4) By key (and optionally by subkey). For example, key =
           dict(study=’some-unique-id’, experiment=’experiment1’, data=’raw’)
        
        In the first case, the file is already on the system, and so the same
        path is returned, unless dest_path is provided, in which case the file
        is copied to dest_path and dest_path is returned.

        In the second case, the local SHA-1 cache is first searched to see if
        the file with the requested SHA-1 is present. If so, that file is used.
        Otherwise, the remote kbucket share (if configured) is searched, as well
        as any alternate kbucket shares, as well as the kbucket share with ID
        specified by the share_id parameter. If found on a kbucket share, the
        file will be downloaded to the SHA-1 cache (or to dest_path if provided)
        and that local path will be returned.

        In the third case, the kbucket server is probed and the SHA-1 hash of
        the file is retrieved. If a file with that checksum is found on the
        local machine, then that is used (or copied to dest_path). Otherwise,
        the file is downloaded from kbucket as above.

        In the fourth case, the SHA-1 hash of the file is first retrieved via
        getValue(key=key) or getValue(key=key, subkey=subkey) and then we follow
        the procedure as the SHA-1 URL as above.

        Parameters
        ----------
        path : str, optional
            The path of the file to realize. This could either be a local path,
            a SHA-1 URL, or a kbucket URL as described above (the default is
            None, in which case key must be specified)
        key : str, optional
            The key used for locating the file as described above (the default
            is None, in which case path must be specified)
        subkey : str, optional
            The optional subkey as described in the docs for getValue() and
            setValue() (the default is None)
        dest_path : str, optional
            The destination path for the realized file on the local system, as
            described above. (The default is None, which means that a temporary
            file will be created as needed)
        local_first : bool, optional
            In the case where key is used (rather than path), specifies whether
            to consult the local database first, prior to requesting the SHA-1
            hash from the remote collection. (The default is None, meaning that
            only the configured database is used)
        
        Returns
        -------
        str or None
            The local file path to the "realized" file, or None if the file was
            not found.
        """
        if path and path.startswith('key://'):
            path = self.resolveKeyPath(path)
            if not path:
                return None

        if path is not None:
            if key is not None:
                raise Exception('Cannot specify both key and path in realizeFile.')
            return self._realize_file(path=path, dest_path=dest_path, show_progress=show_progress, download_from=download_from)
        elif key is not None:
            val = self.getValue(key=key, subkey=subkey, local_first=local_first, collection=collection)
            if not val:
                return None
            return self.realizeFile(path=val, dest_path=dest_path, show_progress=show_progress, download_from=download_from)
        else:
            raise Exception('Missing key or path in realizeFile().')

    @mtlogging.log(name='MountainClient:saveFile')
    def saveFile(self, path=None, *, key=None, subkey=None, collection=None, basename=None, local_also=False, upload_to=None):
        """
        Save a file to the local SHA-1 cache and/or upload to a remote KBucket
        share, and return a SHA-1 URL referring to the file.

        If the client is configured via configLocal() or configRemoteReadonly(),
        then the file is only saved to the local SHA-1 cache.

        If the client is configured via configRemoteReadWrite(), then the file
        is uploaded (if needed) to the remote KBucket share. If local_also=True
        then the file is also saved to the local SHA-1 cache.

        The file is specified using either path or key, as described in the
        documentation for realizeFile().
        
        Parameters
        ----------
        path : str, optional
            The path of the file. This could either be a local path, a SHA-1
            URL, or a kbucket URL as described in the docs for realizeFile()
            (the default is None, in which case key must be specified)
        key : str, optional
            The key used for locating the file as described in the docs for
            realizeFile() (the default is None, in which case path must be
            specified)
        subkey : str, optional
            The optional subkey as described in the docs for getValue() and
            setValue() (the default is None)
        basename : str, optional
            An optional basename to be used in constructing the SHA-1 URL.
        local_also : bool, optional
            Whether to also save locally, if configured to save remotely (the
            default is False)
        
        Returns
        -------
        str or None
            A SHA-1 URL for the saved or uploaded file, or None if the file was
            unable to be saved.
        """
        if path and path.startswith('key://'):
            path = self.resolveKeyPath(path)
            if not path:
                return None

        if path is None:
            self.setValue(key=key, subkey=subkey, collection=collection,
                          value=None, local_also=local_also)
            return None
        sha1_path = self._save_file(
            path=path, basename=basename, upload_to=upload_to)
        if key is not None:
            self.setValue(key=key, subkey=subkey, collection=collection,
                          value=sha1_path, local_also=local_also)

        return sha1_path

    # load object / save object
    @mtlogging.log(name='MountainClient:loadObject')
    def loadObject(self, *, key=None, path=None, subkey=None, local_first=False, collection=None, download_from=None):
        if path and path.startswith('key://'):
            path = self.resolveKeyPath(path)
            if not path:
                return None
        
        txt = self.loadText(key=key, path=path,
                            subkey=subkey, local_first=local_first, collection=collection, download_from=download_from)
        if txt is None:
            return None
        try:
            return json.loads(txt)
        except:
            print('WARNING: unable to parse json in loadObject.', path, key, subkey)
            return None

    def saveObject(self, object, *, key=None, subkey=None, basename='object.json', local_also=False, dest_path=None, collection=None, upload_to=None):
        if object is None:
            self.setValue(key=key, subkey=subkey, collection=collection,
                          value=None),
            return None
        return self.saveText(text=json.dumps(object), key=key, collection=collection, subkey=subkey, basename=basename, local_also=local_also, dest_path=dest_path, upload_to=upload_to)

    def createSnapshot(self, path, *, upload_to=None, download_recursive=False, upload_recursive=False, dest_path=None):
        if path and path.startswith('key://'):
            path = self.resolveKeyPath(path)
            if not path:
                print('Unable to resolve key path.', file=sys.stderr)
                return None

        if self.isFile(path):
            address = client.saveFile(path=path)
            if not address:
                print('Unable to read or save file', file=sys.stderr)
                return None
            if upload_to:
                if not self.saveFile(path=path, upload_to=upload_to):
                    print('Unable to upload file', file=sys.stderr)
                    return None
        else:
            dd = self.readDir(path=path, recursive=True, include_sha1=True)
            if not dd:
                print('Unable to read file or directory', file=sys.stderr)
                return None
            if self.isLocalPath(path) or download_recursive:
                if not self._create_snapshot_helper_save_dd(basepath=path, dd=dd, upload_to=None):
                    print('Problem saving files to local cache.')
                    return None
                if upload_to and upload_recursive:
                    if not self._create_snapshot_helper_save_dd(basepath=path, dd=dd, upload_to=upload_to):
                        print('Problem saving files to local cache.')
                        return None

            address = self.saveObject(dd, basename='')
            address = address.replace('sha1://', 'sha1dir://')
            if upload_to:
                self.saveObject(dd, upload_to=upload_to)
        if address and dest_path:
            if dest_path.startswith('key://'):
                location, collection, key, subkey, extra_path = self._parse_key_path(dest_path)
                if not location:
                    raise Exception('Error parsing key path', dest_path)
                if extra_path:
                    raise Exception('Invalid key path for storage', dest_path)
                if location == 'local':
                    if collection != 'default':
                        raise Exception('Collection must be default for local key path.', collection)
                    collection = None
                elif location == 'pairio':
                    pass
                else:
                    raise Exception('Invalid location for key path', location)

                if not self.setValue(key=key, subkey=subkey, value=address, collection=collection):
                    raise Exception('Unable to store address in path', dest_path)
            else:
                self.realizeFile(path=address, dest_path=dest_path)

        return address

    def resolveKeyPath(self, key_path):
        if not key_path.startswith('key://'):
            return key_path
        location, collection, key, subkey, extra_path = self._parse_key_path(key_path)
        
        if location == 'local':
            if collection != 'default':
                print('Warning: Invalid key path local collection', collection)
                return False
            local_client = MountainClient()
            val = local_client.getValue(key=key, subkey=subkey)
        elif location == 'pairio':
            val = self.getValue(key=key, subkey=subkey, collection=collection)
        else:
            print('Warning: Invalid key path location', location)
            return None
        if val is None:
            return None
        if not (val.startswith('sha1://') or val.startswith('sha1dir://')):
            print('Warning: Invalid value when resolving key path', val)
            return val
        if extra_path:
            val = val + '/' + extra_path
        return val

    def _parse_key_path(self, key_path):
        list0 = key_path.split('/')
        if len(list0) < 5:
            return (None, None, None, None, None)
        location = list0[2]
        collection = list0[3]
        key = list0[4]
        if ':' in key:
            vals0 = key.split(':')
            if len(vals0) != 2:
                return (None, None, None, None, None)
            key = vals0[0]
            subkey = vals0[1]
        else:
            subkey = None
        extra_path = '/'.join(list0[5:])
        return (location, collection ,key, subkey, extra_path)

    def _create_snapshot_helper_save_dd(self, *, basepath, dd, upload_to):
        for fname in dd['files'].keys():
            fpath = os.path.join(basepath, fname)
            if not self.saveFile(path=fpath, upload_to=upload_to):
                if not upload_to:
                    print('Unable to copy file to local cache: '+fpath, file=sys.stderr)
                else:
                    print('Unable to upload file: '+fpath, file=sys.stderr)
                return False
        for dname, dd0 in dd['dirs'].items():
            dpath = os.path.join(basepath, dname)
            if not self._create_snapshot_helper_save_dd(basepath=dpath, dd=dd0, upload_to=upload_to):
                return False
        return True

    # load text / save text
    @mtlogging.log(name='MountainClient:loadText')
    def loadText(self, *, key=None, path=None, subkey=None, local_first=False, collection=None, download_from=None):
        if path and path.startswith('key://'):
            path = self.resolveKeyPath(path)
            if not path:
                return None

        fname = self.realizeFile(
            key=key, path=path, subkey=subkey, local_first=local_first, collection=collection, download_from=download_from)
        if fname is None:
            return None
        try:
            with open(fname) as f:
                return f.read()
        except:
            print('Unexpected problem reading file in loadText: '+fname)
            return None

    @mtlogging.log(name='MountainClient:saveText')
    def saveText(self, text, *, key=None, subkey=None, collection=None, basename='file.txt', local_also=False, dest_path=None, upload_to=None):
        if text is None:
            self.setValue(key=key, subkey=subkey,
                          value=None, local_also=local_also, collection=collection)
            return None
        if dest_path is None:
            tmp_fname = _create_temporary_file_for_text(text=text)
        else:
            with open(dest_path, 'w') as f:
                f.write(text)
            tmp_fname=dest_path
        try:
            ret = self.saveFile(tmp_fname, key=key, subkey=subkey, collection=collection,
                                basename=basename, local_also=local_also, upload_to=upload_to)
        except:
            if dest_path is None:
                os.unlink(tmp_fname)
            raise
        if dest_path is None:
            os.unlink(tmp_fname)
        return ret

    @mtlogging.log(name='MountainClient:readDir')
    def readDir(self, path, recursive=False, include_sha1=True, download_from=None):
        if path and path.startswith('key://'):
            path = self.resolveKeyPath(path)
            if not path:
                return None

        if path.startswith('kbucket://'):
            path_local = self._local_db._find_file_in_local_kbucket_share(path, directory=True)
            if path_local is not None:
                return self.readDir(path=path_local, recursive=recursive, include_sha1=include_sha1)

            list0 = path.split('/')
            kbucket_share_id = list0[2]
            path0 = '/'.join(list0[3:])
            if kbucket_share_id and ('.' in kbucket_share_id):
                tmp0 = kbucket_share_id
                kbucket_share_id=self._get_value_from_alias(kbucket_share_id)
                if kbucket_share_id is None:
                    print('Warning: unable to resolve kbucket alias: ' + tmp0)
                    return None
            ret = self._read_kbucket_dir(
                share_id=kbucket_share_id, path=path0, recursive=recursive, include_sha1=include_sha1)
        elif path.startswith('sha1dir://'):
            list0 = path.split('/')
            sha1 = list0[2]
            if '.' in sha1: sha1=sha1.split('.')[0]
            dd = self.loadObject(path='sha1://'+sha1, download_from=download_from)
            if not dd:
                return None
            ii = 3
            while ii < len(list0):
                name0 = list0[ii]
                if name0 in dd['dirs']:
                    dd = dd['dirs'][name0]
                else:
                    return None
                ii=ii+1
            return dd
        else:
            ret = self._read_file_system_dir(
                path=path, recursive=recursive, include_sha1=include_sha1)
        return ret

    @mtlogging.log(name='MountainClient:computeDirHash')
    def computeDirHash(self, path):
        if path and path.startswith('key://'):
            # todo
            raise Exception('This case not handled yet')

        if path in _global_kbucket_mem_dir_hash_cache:
            return _global_kbucket_mem_dir_hash_cache[path]
        dd = self.readDir(path=path, recursive=True, include_sha1=True)
        ret = _sha1_of_object(dd)
        if ret:
            _global_kbucket_mem_dir_hash_cache[path] = ret
        return ret

    @mtlogging.log(name='MountainClient:computeFileSha1')
    def computeFileSha1(self, path):
        if path and path.startswith('key://'):
            path = self.resolveKeyPath(path)
            if not path:
                return None

        return self._local_db.computeFileSha1(path=path)
    
    def sha1OfObject(self, obj):
        return _sha1_of_object(obj)

    @mtlogging.log(name='MountainClient:computeFileOrDirHash')
    def computeFileOrDirHash(self, path):
        if path and (path.startswith('kbucket://') or path.startswith('sha1dir://') or path.startswith('key://')):
            if self.findFile(path):
                return self.computeFileSha1(path)
            else:
                return self.computeDirHash(path)
        elif path.startswith('sha1://'):
            return self.computeFileSha1(path)
        else:
            if os.path.isdir(path):
                return self.computeDirHash(path)
            else:
                return self.computeFileSha1(path)

    def isFile(self, path):
        if self.isLocalPath(path=path):
            return os.path.isfile(path)
        if path.startswith('sha1://'):
            return True
        elif path.startswith('kbucket://') or path.startswith('sha1dir://') or path.startswith('key://'):
            return (self.computeFileSha1(path) is not None)
        else:
            return os.path.isfile(path)

    def isLocalPath(self, path):
        # rename to isLocalFilePath
        if path.startswith('sha1://') or path.startswith('sha1dir://') or path.startswith('kbucket://') or path.startswith('key://'):
            return False
        return True

    def localCacheDir(self):
        return self._local_db.localCacheDir()

    def alternateLocalCacheDirs(self):
        return self._local_db.alternateLocalCacheDirs()

    @mtlogging.log(name='MountainClient:findFileBySha1')
    def findFileBySha1(self, *, sha1, download_from=None, local_only=False):
        return self._realize_file(path='sha1://'+sha1, resolve_locally=False, local_only=local_only, download_from=download_from)

    @mtlogging.log(name='MountainClient:getSha1Url')
    def getSha1Url(self, path, *, basename=None):
        if basename is None:
            basename = os.path.basename(path)

        sha1 = self.computeFileSha1(path)
        if not sha1:
            return None

        return 'sha1://{}/{}'.format(sha1, basename)
        

    @mtlogging.log(name='MountainClient:findFile')
    def findFile(self, path, local_only=False, download_from=None):
        if path and path.startswith('key://'):
            path = self.resolveKeyPath(path)
            if not path:
                return None
        return self._realize_file(path=path, resolve_locally=False, local_only=local_only, download_from=download_from)

    @mtlogging.log(name='MountainClient:copyToLocalCache')
    def copyToLocalCache(self, path, basename=None):
        if path and path.startswith('key://'):
            path = self.resolveKeyPath(path)
            if not path:
                return None
        return self._save_file(path=path, return_sha1_url=False, basename=basename)

    def _initialize_kacheries(self):
        kacheries_fname=os.path.join(os.environ.get('HOME',''),'.mountaintools', 'kacheries')
        kachery_upload_tokens_fname=os.path.join(os.environ.get('HOME',''),'.mountaintools', 'kachery_upload_tokens')
        kachery_urls = dict()
        kachery_upload_tokens = dict()
        if os.path.exists(kacheries_fname):
            txt = _read_text_file(kacheries_fname)
            lines = txt.splitlines()
            for line in lines:
                if not line.startswith('#'):
                    vals = line.split()
                    if len(vals) != 2:
                        print('WARNING: problem parsing kacheries file.')
                    else:
                        kachery_urls[vals[0]] = vals[1]
        if os.path.exists(kachery_upload_tokens_fname):
            txt = _read_text_file(kachery_upload_tokens_fname)
            lines = txt.splitlines()
            for line in lines:
                if not line.startswith('#'):
                    vals = line.split()
                    if len(vals) != 2:
                        print('WARNING: problem parsing kachery_upload_tokens file.')
                    else:
                        kachery_upload_tokens[vals[0]] = vals[1]
        for name, url in kachery_urls.items():
            self._kachery_urls[name] = url
        for name, token in kachery_upload_tokens.items():
            self._kachery_upload_tokens[name] = token
            

    def _read_pairio_tokens(self):
        pairio_tokens_fname=os.path.join(os.environ.get('HOME',''),'.mountaintools', 'pairio_tokens')
        if os.path.exists(pairio_tokens_fname):
            txt = _read_text_file(pairio_tokens_fname)
            lines = txt.splitlines()
            for line in lines:
                if not line.startswith('#'):
                    vals = line.split()
                    if len(vals) != 2:
                        print('WARNING: problem parsing pairio tokens file.')
                    else:
                        self._pairio_tokens[vals[0]] = vals[1]

    def _get_value(self, *, key, subkey, collection=None, local_first=False, check_alt=False):
        if local_first or not collection:
            ret = self._local_db.getValue(key=key, subkey=subkey, check_alt=check_alt)
            if ret is not None:
                return ret
        if collection:
            ret = self._remote_client.getValue(
                key=key, subkey=subkey, collection=collection, url=self._pairio_url)
            if ret is not None:
                return ret
        return None

    def _get_value_from_alias(self, alias):
        if alias in self._values_by_alias:
            return self._values_by_alias[alias]
        vals=alias.split('.')
        if len(vals)!=2:
            raise Exception('Invalid alias: ' + alias)
        ret=self.getValue(key=vals[1], collection=vals[0])
        if ret is None:
            return None
        self._values_by_alias[alias]=ret
        return ret

    def _set_value(self, *, key, subkey, value, overwrite, local_also=False, collection=None):
        if collection:
            token = self._pairio_tokens.get(collection, None)
        else:
            token = None
        if collection and (not token):
            raise Exception('Unable to set value... no token found for collection {}'.format(collection)) # should we throw an exception here?
        if local_also or (not collection):
            if not self._local_db.setValue(key=key, subkey=subkey, value=value, overwrite=overwrite):
                return False
        if collection:
            if not self._remote_client.setValue(key=key, subkey=subkey, value=value, overwrite=overwrite, collection=collection, url=self._pairio_url, token=token):
                raise Exception('Error setting value to remote collection {}'.format(collection))
        return True

    def _get_sub_keys(self, *, key, collection):
        if collection:
            return self._remote_client.getSubKeys(key=key, collection=collection, url=self._pairio_url)
        else:
            return self._local_db.getSubKeys(key=key)

    def _realize_file(self, *, path, resolve_locally=True, local_only=False, dest_path=None, show_progress=False, download_from=None):
        ret = self._local_db.realizeFile(
            path=path, local_only=local_only, resolve_locally=resolve_locally, dest_path=dest_path, show_progress=show_progress)
        if ret:
            return ret
        if local_only:
            return None
        download_froms = []
        if download_from is not None:
            download_froms.append(download_from)
        for kname in self._config_download_from:
            download_froms.append(kname)
        if path.startswith('sha1://'):
            list0 = path.split('/')
            sha1 = list0[2]
            for df0 in download_froms:
                url, size = self._find_on_kachery_or_kbucket(download_from=df0, sha1=sha1)
                if url:
                    if resolve_locally:
                        return self._local_db.realizeFileFromUrl(url=url, sha1=sha1, size=size, dest_path=dest_path, show_progress=show_progress)
                    else:
                        return url
        return None

    @mtlogging.log()
    def _save_file(self, *, path, basename, return_sha1_url=True, upload_to=None):
        path = self.realizeFile(path)
        if not path:
            return None
        ret = self._local_db.saveFile(
            path=path, basename=basename, return_sha1_url=return_sha1_url)
        if not ret:
            return None
        if upload_to:
            sha1 = self.computeFileSha1(path=ret)
            kachery_url = self._resolve_kachery_url(upload_to)
            if not kachery_url:
                raise Exception('Unable to resolve kachery url for: {}'.format(upload_to))
            if upload_to not in self._kachery_upload_tokens.keys():
                raise Exception('Kachery upload token not found for: {}'.format(upload_to))
            kachery_upload_token=self._kachery_upload_tokens[upload_to]
            self._upload_to_kachery(path=path, sha1=sha1, kachery_url=kachery_url, upload_token=kachery_upload_token)
        return ret
    
    def _resolve_kachery_url(self, name):
        if name.startswith('http://') or name.startswith('https://'):
            return name
        if '.' in name:
            return self._get_value_from_alias(name)
        if name not in self._kachery_urls.keys():
            return None
        return self._kachery_urls[name]

    def _upload_to_kachery(self, *, path, sha1, kachery_url, upload_token):
        url_check_path0 = '/check/sha1/'+sha1
        url_check = kachery_url+url_check_path0
        resp_obj = _http_get_json(url_check)
        if not resp_obj['success']:
            print('Warning: Problem checking for upload: '+resp_obj['error'])
            return False

        if not resp_obj['found']:
            url_path0 = '/set/sha1/'+sha1
            signature = _sha1_of_object(
                {'path': url_path0, 'token': upload_token})
            url = kachery_url+url_path0+'?signature='+signature
            size0 = os.path.getsize(path)
            if size0 > 10000:
                print(
                    'Uploading to kachery --- ({}): {} -> {}'.format(_format_file_size(size0), path, url))

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
            print('Already on server (***)')
            return True

    def _find_on_kachery_or_kbucket(self, *, download_from, sha1):
        assert download_from

        kachery_url = self._resolve_kachery_url(download_from)

        if kachery_url:
            check_url = kachery_url + '/check/sha1/' + sha1
            try:
                obj = _http_get_json(check_url)
            except:
                print('WARNING: failed in check to kachery {}: {}'.format(download_from, check_url))
                return (None, None)
            if not obj['success']:
                print('WARNING: problem checking kachery {}: {}'.format(download_from, check_url))
                return (None, None)
            if not obj['found']:
                return (None, None)
            return (kachery_url + '/get/sha1/' + sha1, obj['size'])
            


        # first check in the upload location
        (sha1_0, size_0, url_0) = self._local_db.getKBucketFileInfo(
            path='kbucket://'+download_from+'/sha1-cache/'+sha1[0:1]+'/'+sha1[1:3]+'/'+sha1)
        if sha1_0 is not None:
            if sha1_0 == sha1:
                return (url_0, size_0)
            else:
                print('Unexpected issue where checksums do not match on _find_on_kachery_or_kbucket: {} <> {}'.format(
                    sha1, sha1_0))

        kbucket_url = self._local_db.kbucketUrl()
        if not kbucket_url:
            return (None, None)
        url = kbucket_url+'/'+download_from+'/api/find/'+sha1
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
        node_info = self._local_db.getNodeInfo(share_id=download_from)
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
                ret['dirs'][name0] = self._read_kbucket_dir(share_id=share_id, path = path+'/'+name0, recursive=True, include_sha1=include_sha1)

        return ret

    def _read_file_system_dir(self, *, path, recursive, include_sha1):
        ret = dict(
            files={},
            dirs={}
        )
        list0 = _safe_list_dir(path)
        if list0 is None:
            return None
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

class MountainClientLocal():
    def __init__(self, parent):        
        self._parent = parent
        self._sha1_cache = Sha1Cache()
        self._kbucket_url = os.getenv(
            'KBUCKET_URL', 'https://kbucket.flatironinstitute.org')
        self._nodeinfo_cache = dict()
        self._local_kbucket_shares = dict()
        self._initialize_local_kbucket_shares()

    def getSubKeys(self, *, key):
        keyhash = _hash_of_key(key)
        subkey_db_path = self._get_subkey_file_path_for_keyhash(keyhash, _create=False)
        if not os.path.exists(subkey_db_path):
            return []
        ret = []
        with FileLock(subkey_db_path+'.lock'):
            list0 = _safe_list_dir(subkey_db_path)
            if list0 is None:
                return None
            for name0 in list0:
                if name0.endswith('.txt'):
                    ret.append(name0[0:-4])
        return ret

    def getValue(self, *, key, subkey=None, check_alt=False, _db_path=None, _disable_lock=False):
        keyhash = _hash_of_key(key)
        if subkey is not None:
            if check_alt:
                raise Exception('Cannot use check_alt together with subkey.')
            if subkey == '-':
                subkeys = self.getSubKeys(key=key)
                obj = dict()
                for subkey in subkeys:
                    val = self.getValue(key=key, subkey=subkey)
                    if val is not None:
                        obj[subkey] = val
                return json.dumps(obj)
            else:
                subkey_db_path = self._get_subkey_file_path_for_keyhash(keyhash, _db_path=_db_path, _create=False)
                fname0 = os.path.join(subkey_db_path, subkey+'.txt')
                if not os.path.exists(fname0):
                    return None
                with FileLock(subkey_db_path+'.lock', _disable_lock=_disable_lock):
                    txt = _read_text_file(fname0)
                    return txt
        else:
            # not a subkey
            db_path = self._get_file_path_for_keyhash(keyhash, _db_path=_db_path, _create=False)
            fname0 = db_path
            if not os.path.exists(fname0):
                if check_alt:
                    alternate_db_paths = self.alternateLocalDatabasePaths()
                    for db_path in alternate_db_paths:
                        val = self.getValue(key=key, subkey=None, check_alt=None, _db_path=db_path, _disable_lock=True)
                        if val:
                            return val
                return None
            with FileLock(fname0+'.lock', _disable_lock=_disable_lock):
                txt = _read_text_file(fname0)
                return txt

    def setValue(self, *, key, subkey, value, overwrite):
        keyhash = _hash_of_key(key)
        if subkey is not None:
            if subkey == '-':
                if value is not None:
                    raise Exception('Cannot set all subkeys with value that is not None')
                subkey_db_path = self._get_subkey_file_path_for_keyhash(keyhash, _create=True)
                with FileLock(subkey_db_path+'.lock'):
                    shutil.rmtree(subkey_db_path)
            else:
                subkey_db_path = self._get_subkey_file_path_for_keyhash(keyhash, _create=True)
                fname0 = os.path.join(subkey_db_path, subkey+'.txt')
                if os.path.exists(fname0):
                    if not overwrite:
                        return False
                with FileLock(subkey_db_path+'.lock'):
                    if os.path.exists(fname0):
                        if not overwrite:
                            return False
                    if value is None:
                        os.unlink(fname0)
                    else:
                        #_write_text_file_safe(fname0, value)
                        _write_text_file(fname0, value)
                return True
        else:
            # not a subkey
            db_path = self._get_file_path_for_keyhash(keyhash, _create=True)
            fname0 = db_path
            if os.path.exists(fname0):
                if not overwrite:
                    return False
            with FileLock(fname0+'.lock'):
                if os.path.exists(fname0):
                    if not overwrite:
                        return False
                if value is None:
                    if os.path.exists(fname0):
                        os.unlink(fname0)
                else:
                    _write_text_file(fname0, value)
            return True

    @mtlogging.log()
    def realizeFile(self, *, path, local_only=False, resolve_locally=True, dest_path=None, show_progress=False):
        if path.startswith('sha1://'):
            list0 = path.split('/')
            sha1 = list0[2]
            return self._realize_file_from_sha1(sha1=sha1, dest_path=dest_path, show_progress=show_progress)
        elif path.startswith('kbucket://'):
            path_local = self._find_file_in_local_kbucket_share(path)
            if path_local is not None:
                return path_local
            sha1, size, url = self._get_kbucket_file_info(path=path)
            if sha1 is None:
                return None
            try_local_path = self._sha1_cache.findFile(sha1)
            if try_local_path is not None:
                return try_local_path
            if local_only:
                return None
            if not resolve_locally:
                return path  # hmmm, should we return url here?
            ret = self._sha1_cache.downloadFile(url=url, sha1=sha1, size=size, show_progress=show_progress)
            if (ret is not None) and (dest_path is not None):
                if os.path.abspath(ret) != os.path.abspath(dest_path):
                    if show_progress:
                        print('Copying file {} -> {}'.format(ret, dest_path))
                    shutil.copyfile(ret, dest_path)
                    self._sha1_cache.reportFileSha1(dest_path, sha1)
                    return dest_path
            return ret
        elif path.startswith('sha1dir://'):
            sha1 = self.computeFileSha1(path=path)
            if not sha1:
                return None
            return self._parent._realize_file(path='sha1://'+sha1, local_only=local_only, resolve_locally=resolve_locally, dest_path=dest_path, show_progress=show_progress)

        # If the file exists on the local computer, just use that
        if os.path.isfile(path):
            if (dest_path is not None) and (os.path.abspath(path)!=os.path.abspath(dest_path)):
                if show_progress:
                    print('Copying file {} -> {}'.format(path, dest_path))
                shutil.copyfile(path, dest_path)
                return os.path.abspath(dest_path)
            return os.path.abspath(path)

        return None

    def realizeFileFromUrl(self, *, url, sha1, size, dest_path=None, show_progress=False):
        return self._sha1_cache.downloadFile(url=url, sha1=sha1, size=size, target_path=dest_path, show_progress=show_progress)

    @mtlogging.log()
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

        if basename:
            ret_path = 'sha1://{}/{}'.format(sha1, basename)
        else:
            ret_path = 'sha1://{}'.format(sha1)
        return ret_path

    @mtlogging.log(name='MountainClientLocal:computeFileSha1')
    def computeFileSha1(self, path):
        if path.startswith('sha1://'):
            list0 = path.split('/')
            sha1 = list0[2]
            return sha1
        elif path.startswith('kbucket://'):
            path_local = self._find_file_in_local_kbucket_share(path)
            if path_local is not None:
                return self.computeFileSha1(path=path_local)
            sha1, _, __ = self._get_kbucket_file_info(path=path)
            return sha1
        elif path.startswith('sha1dir://'):
            list0 = path.split('/')
            sha1 = list0[2]
            if '.' in sha1: sha1=sha1.split('.')[0]
            dd = self._parent.loadObject(path='sha1://'+sha1)
            if not dd:
                return None
            ii = 3
            while ii < len(list0):
                name0 = list0[ii]
                if name0 in dd['dirs']:
                    dd = dd['dirs'][name0]
                elif name0 in dd['files']:
                    if ii+1 == len(list0):
                        sha1 = dd['files'][name0]['sha1']
                        return sha1
                    else:
                        return None
                else:
                    return None
                ii=ii+1
            return None
        else:
            return self._sha1_cache.computeFileSha1(path=path)

    def getNodeInfo(self, *, share_id):
        return self._get_node_info(share_id=share_id)

    def getKBucketUrlForShare(self, *, share_id):
        return self._get_kbucket_url_for_share(share_id=share_id)

    def kbucketUrl(self):
        return self._kbucket_url

    def localCacheDir(self):
        return self._sha1_cache.directory()

    def alternateLocalCacheDirs(self):
        return self._sha1_cache.alternateDirectories()

    def localDatabasePath(self):
        return _get_default_local_db_path()

    def alternateLocalDatabasePaths(self):
        return _get_default_alternate_local_db_paths()

    def _initialize_local_kbucket_shares(self):
        local_kbucket_shares_fname=os.path.join(os.environ.get('HOME',''),'.mountaintools', 'local_kbucket_shares')
        if os.path.exists(local_kbucket_shares_fname):
            txt=_read_text_file(local_kbucket_shares_fname)
            lines=txt.splitlines()
            for path0 in lines:
                if os.path.isdir(path0):
                    kbucket_config_path=os.path.join(path0, '.kbucket')
                    if os.path.isdir(kbucket_config_path):
                        kbnode_fname=os.path.join(kbucket_config_path, 'kbnode.json')
                        obj = _read_json_file(kbnode_fname)
                        share_id=obj['node_id']
                        self._local_kbucket_shares[share_id]=dict(path=path0)
                    else:
                        print('WARNING: Parsing {}: No such config directory: {}'.format(local_kbucket_shares_fname, kbucket_config_path))    
                else:
                    print('WARNING: Parsing {}: No such directory: {}'.format(local_kbucket_shares_fname, path0))

    def _find_file_in_local_kbucket_share(self, path, directory=False):
        list0 = path.split('/')
        share_id = list0[2]
        path0 = '/'.join(list0[3:])
        if share_id in self._local_kbucket_shares:
            fname = os.path.join(self._local_kbucket_shares[share_id]['path'], path0)
            if directory:
                if os.path.isdir(fname):
                    return fname
            else:
                if os.path.isfile(fname):
                    return fname
        return None

    def _get_file_path_for_keyhash(self, keyhash, *, _create, _db_path=None):
        if _db_path:
            database_path = _db_path
        else:
            database_path = self.localDatabasePath()
        path=os.path.join(database_path, keyhash[0:2], keyhash[2:4])
        if _create:
            if not os.path.exists(path):
                try:
                    os.makedirs(path)
                except:
                    if not os.path.exists(path):
                        raise Exception('Unexpected problem. Unable to create directory: '+path)
        return os.path.join(path, keyhash)

    def _get_subkey_file_path_for_keyhash(self, keyhash, *, _create, _db_path=None):
        if _db_path:
            database_path = _db_path
        else:
            database_path = self.localDatabasePath()
        path=os.path.join(database_path, keyhash[0:2], keyhash[2:4], keyhash+'.dir')
        if _create:
            if not os.path.exists(path):
                try:
                    os.makedirs(path)
                except:
                    if not os.path.exists(path):
                        raise Exception('Unexpected problem. Unable to create directory: '+path)
        return path

    def _realize_file_from_sha1(self, *, sha1, dest_path=None, show_progress=False):
        fname = self._sha1_cache.findFile(sha1)
        if fname is not None:
            if (dest_path is not None) and (os.path.abspath(fname) != os.path.abspath(dest_path)):
                if show_progress:
                    print('Copying file {} -> {}'.format(fname, dest_path))
                shutil.copyfile(fname, dest_path)
                self._sha1_cache.reportFileSha1(dest_path, sha1)
                return os.path.abspath(dest_path)
            return os.path.abspath(fname)
        return None

    def _get_node_info(self, *, share_id):
        if not share_id:
            raise Exception('Cannot get node info for share_id: '+share_id)
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
                #print(
                #    'Testing whether share {} is directly accessible...'.format(share_id))
                node_info['accessible'] = _test_url_accessible(
                    url00, timeout=2)
                if node_info['accessible']:
                    # print('Share {} is directly accessible.'.format(share_id))
                    pass
                else:
                    print('Share {} is not directly accessible (using hub).'.format(share_id))
        return node_info

    def _get_kbucket_url_for_share(self, *, share_id):
        if not share_id:
            raise Exception('Cannot get kbucket url for share: '+share_id)
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


def _db_load(path, *, count=0):
    if count>10:
        raise Exception('Unexpected problem loading database file: '+path)
    if os.path.exists(path):
        try:
            db_txt = _read_text_file(path)
        except:
            if os.path.exists(path):
                raise Exception('Unable to read database file: '+path)
            else:
                return dict()
        try:
            db = json.loads(db_txt)
        except:
            if os.path.exists(path+'.save'):
                print('Warning: Problem parsing json in database file (restoring saved file): '+path)
                try:
                    os.rename(path+'.save',path)
                except:
                    print('Warning: problem renaming .save file. Deleting')
                    try:
                        os.unlink(path+'.save')
                    except:
                        pass
                    try:
                        os.unlink(path)
                    except:
                        pass
            else:
                print('Warning: Problem parsing json in database file (deleting): '+path)
                try:
                    os.unlink(path)
                except:
                    pass
            return _db_load(path, count=count+1)
        return db
    else:
        return dict()
    

def _db_save(path, db):
    # create a backup first
    if os.path.exists(path):
        try:
            # make sure it is good before doing the backup
            _read_json_file(path) # if not good, we get an exception
            if os.path.exists(path+'.save'):
                os.unlink(path+'.save')
            shutil.copyfile(path,path+'.save')
        except:
            # worst case, let's just proceed
            pass
    _write_json_file(db, path)

# def _db_acquire_lock(path, count=0):
#     if count>5:
#         # If we have failed to acquire the lock after this many retries,
#         # let's wait a random amount of time before proceeding
#         print('Warning: having trouble acquiring lock for database file: '+path)
#         time.sleep(random.uniform(1,2))
#     elif count>10:
#         # If we have failed to acquire the lock after this many retries,
#         # then it is a failure
#         raise Exception('Error acquiring lock for database file: '+path)

#     if not os.path.exists(path+'.lock'):
#         tmp_fname=path+'.lock.'+_random_string(6)
#         try:
#             with open(tmp_fname,'w') as f:
#                 f.write('lock file for database')
#         except:
#             raise Exception('Unable to write temporary file for database lock file: '+tmp_fname)
#         if os.path.exists(path+'.lock'):
#             # now suddenly it exists... let's retry
#             os.unlink(tmp_fname)
#             return _db_acquire_lock(path, count+1)
#         try:
#             os.rename(tmp_fname, path+'.lock')
#         except:
#             # cannot rename -- maybe it suddenly exists. Retry
#             os.unlink(tmp_fname)
#             return _db_acquire_lock(path, count+1)
#         if not os.path.exists(path+'.lock'):
#             raise Exception('Unexpected problem acquiring lock. File does not exist: '+path+'.lock')
#         # we got the lock!
#         print('Locked!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!',path)
#         return True
#     else:
#         # the lock file exists, let's see how old it is
#         try:
#             file_mod_time = os.stat(path+'.lock').st_mtime
#         except:
#             # maybe the lock file has disappeared... let's retry
#             return _db_acquire_lock(path, count+1)
#         file_age = time.time() - file_mod_time
#         if file_age > 1:
#             # older than one second is considered stale
#             print('Warning: removing stale database lock file: '+path+'.lock')
#             try:
#                 os.unlink(path+'.lock')
#             except:
#                 # maybe the file has disappeared... we are retrying anyway
#                 pass
#             return _db_acquire_lock(path, count+1)
#         if file_age > 0.1:
#             # The file is not stale yet, but we suspect it is going to become stale
#             # so let's wait a second before retrying
#             time.sleep(1)
#             return _db_acquire_lock(path, count+1)
#         # Otherwise we are going to wait a short random amount of time and then retry
#         time.sleep(random.uniform(0,0.1))
#         return _db_acquire_lock(path, count+1)

# def _db_release_lock(path):
#     if not os.path.exists(path+'.lock'):
#         raise Exception('Cannot release lock. Lock file does not exist: '+path+'.lock')

#     try:
#         os.unlink(path+'.lock')
#     except:
#         raise Exception('Problem deleting database lock file: '+path+'.lock')
#     print('Unlocked!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!',path)


def _read_json_file(path):
    with open(path) as f:
        return json.load(f)

def _read_text_file(path):
    with open(path) as f:
        return f.read()


def _write_json_file(obj, path):
    with open(path, 'w') as f:
        return json.dump(obj, f)

def _write_text_file(fname,txt):
    with open(fname,'w') as f:
        f.write(txt)


def _get_default_local_db_path():
    dir_old=str(pathlib.Path.home())+'/.cairio'
    dir_new=str(pathlib.Path.home())+'/.mountain'
    if os.path.exists(dir_old) and (not os.path.exists(dir_new)):
        print('Moving config directory: {} -> {}'.format(dir_old, dir_new))
        shutil.move(dir_old, dir_new)
    default_dirname = dir_new
    dirname=os.environ.get('MOUNTAIN_DIR',os.environ.get('CAIRIO_DIR', default_dirname))
    if not os.path.exists(dirname):
        try:
            os.mkdir(dirname)
        except:
            # maybe it was created in a different process
            if not os.path.exists(dirname):
                raise
    ret = dirname+'/database'
    return ret

def _is_http_url(url):
    return url.startswith('http://') or url.startswith('https://')

def _get_default_alternate_local_db_paths():
    val = os.environ.get('MOUNTAIN_DIR_ALT',None)
    if not val:
        return []
    dirnames = val.split(':')
    return [dirname+'/database' for dirname in dirnames]


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
    if not os.path.exists(tempdir):
        os.makedirs(tempdir)
    return tempdir+'/tmp_mountainclient_'+''.join(random.choices('abcdefghijklmnopqrstuvwxyz', k=10))+ext

def _random_string(num):
    return ''.join(random.choices('abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ', k=num))


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
        return None

# The global module client
_global_client = MountainClient()
client = _global_client

# if os.environ.get('CAIRIO_CONFIG'):
#     print('configuring cairio...')
#     a = os.environ.get('CAIRIO_CONFIG').split('.')
#     password = os.environ.get('CAIRIO_CONFIG_PASSWORD', None)
#     client.autoConfig(collection=a[0], key=a[1], password=password)
# if os.environ.get('CAIRIO_ALTERNATE_SHARE_IDS'):
#     tmp = os.environ.get('CAIRIO_ALTERNATE_SHARE_IDS')
#     list0 = tmp.split(',')
#     client.setRemoteConfig(alternate_share_ids=list0)
