import json
import os
import sys
import requests
import traceback
from .mountainremoteclient import MountainRemoteClient
from .mountainremoteclient import _http_get_json
import time
import mtlogging
from .aux import _read_text_file, _sha1_of_object, _create_temporary_fname
from .aux import deprecated
from typing import Union, List, Any, Optional, Tuple
from .mttyping import StrOrStrList, StrOrDict
from .mountainclientlocal import MountainClientLocal

env_path = os.path.join(os.environ.get('HOME', ''), '.mountaintools', '.env')
if os.path.exists(env_path):
    try:
        from dotenv import load_dotenv
    except:
        raise Exception(
            'Unable to import dotenv. Use pip install python-dotenv')
    load_dotenv(dotenv_path=env_path, verbose=True)

_global_kbucket_mem_sha1_cache: dict = dict()
_global_kbucket_mem_dir_hash_cache: dict = dict()


class MountainClient():
    """
    MountainClient is a Python client for accessing local and remote kachery and
    pairio databases. All I/O for MountainTools is handled using this client.

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

        # Similarly we can store Python dicts via json content
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
        """
        Create a MountainClient object. Initializes pairio using environment variables.
        """
        self._pairio_url = os.environ.get(
            'MOUNTAIN_URL', os.environ.get('PAIRIO_URL', os.environ.get('CAIRIO_URL', 'http://pairio.org')))
        self._kachery_urls = dict()
        self._kachery_upload_tokens = dict()
        self._kachery_download_tokens = dict()
        self._pairio_tokens = dict()
        self._verbose = None  # None might become true or false depending on env variables
        self._remote_client = MountainRemoteClient()
        self._values_by_alias = dict()
        self._config_download_from = []
        self._local_db = MountainClientLocal(parent=self)

        self._initialize_kacheries()
        self._read_pairio_tokens()

    @deprecated("Warning: login() is deprecated.")
    def login(self, *, user=None, password=None, interactive=False, ask_password=False) -> None:
        pass

    def setPairioToken(self, collection: str, token: str) -> None:
        """
        Store a pairio token for a given collection.
        """
        self._pairio_tokens[collection] = token

    def setKacheryUploadToken(self, kachery_name: str, token: str) -> None:
        """
        Store upload token for given kachery
        """
        self._kachery_upload_tokens[kachery_name] = token

    def setKacheryDownloadToken(self, kachery_name: str, token: str) -> None:
        """
        Store download token for given kachery
        """
        self._kachery_download_tokens[kachery_name] = token

    def addRemoteCollection(self, collection: str, token: str, admin_token: str) -> bool:
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

    def configDownloadFrom(self, kachery_names: StrOrStrList) -> None:
        """
        Configure uris to download entities from.

        Parameters
        ----------
        kachery_names : str or iterable
            Kachery names to enable
        """
        if type(kachery_names) == str:
            kachery_names = [str(kachery_names)]
        for kname in kachery_names:
            if kname not in self._config_download_from:
                self._config_download_from.append(kname)

    def configVerbose(self, value: bool) -> None:
        """Toggle on or off verbose mode

        Parameters
        ----------
        value : bool
            Whether to turn on verbose mode
        """
        self._verbose = value
        self._local_db.configVerbose(value)

    # def getDownloadFromConfig(self):
    #     return deepcopy(dict(
    #         download_from=self._config_download_from
    #     ))

    # def setDownloadFromConfig(self, obj):
    #     self._config_download_from = obj.get('download_from', [])

    @mtlogging.log(name='MountainClient:getValue')
    def getValue(self, *, key: StrOrDict, subkey: Optional[str]=None, parse_json: bool=False, collection: Optional[str]=None, local_first: bool=False, check_alt: bool=False) -> Optional[str]:
        """
        Retrieve a string value from the local database or, if connected to a
        remote mountain collection, from a remote database. This is used to
        retrieve relatively small strings (generally fewer than 80 characters)
        that were previously associated with keys via setValue(). The keys can
        either be strings or Python dicts. In addition to keys, subkeys may also
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
    def setValue(self, *, key: StrOrDict, subkey: Optional[str]=None, value: Union[str, None], overwrite: bool=True, local_also: bool=False, collection: Optional[str]=None) -> bool:
        """
        Store a string value to the local database or, if connected to a remote
        mountain collection, to a remote database. This is used to store
        relatively small strings (generally fewer than 80 characters) and
        associate them with keys for subsequent retrieval using getValue(). The
        keys can either be strings or Python dicts. In addition to keys, subkeys
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
    def getSubKeys(self, key: StrOrDict, collection: str=None) -> Optional[List[str]]:
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
        return self._get_sub_keys(key=key, collection=collection)

    @mtlogging.log(name='MountainClient:realizeFile')
    def realizeFile(self, path: Optional[str]=None, *, key: Optional[StrOrDict]=None, subkey: Optional[str]=None, dest_path: Optional[str]=None,
                    local_first: bool=False, show_progress: bool=False, collection: Optional[str]=None,
                    download_from: Optional[StrOrStrList]=None, local_only: bool=False, remote_only: bool=False) -> Optional[str]:
        """
        Return a local path to the specified file, downloading the file from a
        remote server to the local SHA-1 cache if needed. In other words,
        "realize" the file on the local file system. There are four ways to
        refer to a file:

        1) By local path. For example, path = '/path/to/local/file.dat'
        2) By SHA-1 URL. For example, path =
           'sha1://7bf5432e9266831ab7d64d193fe3f8c69c9e04cc/experiment1/raw.dat'
        3) By sha1 directory URL. For example, path =
           'sha1dir://fb52d510d2543634e247e0d2d1d4390be9ed9e20.synth_magland/001_synth/params.json'
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

        TODO: describe the third case... sha1://

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
        show_progress : bool, optonal
            If True, displays information about the files being copied
        collection : str, optional
            The name of the collection to retrieve the value from, which may be
            different from the collection specified in configRemoteReadonly()
            configRemoteReadWrite() (the default is None, which means that the
            configured collection is used)
        download_from : str, optional
            If present, points to the kachery server to download the file from
        local_only : bool, optional
            If True, only search for the file locally (default False)
        remote_only : bool, optional
            If True, only search for the file remotely (default False)
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
                raise Exception(
                    'Cannot specify both key and path in realizeFile.')
            return self._realize_file(path=path, dest_path=dest_path, show_progress=show_progress, download_from=download_from, local_only=local_only, remote_only=remote_only)
        elif key is not None:
            val = self.getValue(key=key, subkey=subkey,
                                local_first=local_first, collection=collection)
            if not val:
                return None
            return self.realizeFile(path=val, dest_path=dest_path, show_progress=show_progress, download_from=download_from, local_only=local_only, remote_only=remote_only)
        else:
            raise Exception('Missing key or path in realizeFile().')

    @mtlogging.log(name='MountainClient:saveFile')
    def saveFile(self, path: Optional[str]=None, *, key: Optional[StrOrDict]=None, subkey: Optional[str]=None, collection: Optional[str]=None, basename: Optional[str]=None, local_also: bool=False, upload_to: Optional[StrOrStrList]=None) -> Optional[str]:
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
        collection : str, optional
            The name of the collection to retrieve the value from, which may be
            different from the collection specified in configRemoteReadonly()
            configRemoteReadWrite() (the default is None, which means that the
            configured collection is used)
        basename : str, optional
            An optional basename to be used in constructing the SHA-1 URL.
        local_also : bool, optional
            Whether to also save locally, if configured to save remotely (the
            default is False)
        upload_to : str, optional
            Name of kachery server to upload the file to

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
    def loadObject(self, *, key: Optional[StrOrDict]=None, path: Optional[str]=None, subkey: Optional[str]=None, local_first: bool=False, collection: Optional[str]=None, download_from: Optional[StrOrStrList]=None, local_only: bool=False, remote_only: bool=False) -> Optional[dict]:
        """
        Return contents of a given JSON file as Python dictionary, downloading the file if necessary.

        Parameters
        ----------
        key : str or dict
            The key used to look up the value
        subkey : str, optional
            A subkey string (the default is None, which means that no subkey is
            used). To retrieve values for all subkeys, use subkey='-'.
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
        dict or None
            Dictionary representing JSON object stored in the file
            or None if data could not be retrieved.
        """
        if path and path.startswith('key://'):
            path = self.resolveKeyPath(path)
            if not path:
                return None

        txt = self.loadText(key=key, path=path,
                            subkey=subkey, local_first=local_first, collection=collection, download_from=download_from, local_only=local_only, remote_only=remote_only)
        try:
            if txt is not None:
                return json.loads(txt)
        except:
            print('WARNING: unable to parse json in loadObject.', path, key, subkey)

        return None

    def saveObject(self, object: dict, *, key: Optional[StrOrDict]=None, subkey: Optional[str]=None, basename: Optional[str]='object.json', local_also: bool=False, dest_path: Optional[str]=None, collection: Optional[str]=None, upload_to: Optional[StrOrStrList]=None, indent: Optional[int]=None) -> Optional[str]:
        """
        Save object into a json file and/or upload it to a remote KBucket share.

        Parameters
        ----------
        object : dict
            Object to be saved.
        key : str, optional
            The key used for locating the file as described in the docs for
            realizeFile()
        subkey : str, optional
            The optional subkey as described in the docs for getValue() and
            setValue() (the default is None)

        Returns
        -------
        str or None
            A SHA-1 URL for the saved or uploaded file, or None if the file was
            unable to be saved.
        """
        if object is None:
            self.setValue(key=key, subkey=subkey, collection=collection,
                          value=None),
            return
        return self.saveText(text=json.dumps(object, indent=indent), key=key, collection=collection, subkey=subkey, basename=basename, local_also=local_also, dest_path=dest_path, upload_to=upload_to)

    def createSnapshots(self, paths, *, upload_to: Optional[StrOrStrList]=None, download_recursive=False, upload_recursive=False, dest_paths=None) -> List[Optional[str]]:
        if dest_paths is None:
            dest_paths = [None for path in paths]
        return [
            self.createSnapshot(path=path, upload_to=upload_to, download_recursive=download_recursive,
                                upload_recursive=upload_recursive, dest_path=dest_paths[ii])
            for ii, path in enumerate(paths)
        ]

    def createSnapshot(self, path: str, *, upload_to: Optional[StrOrStrList]=None, download_recursive=False, upload_recursive=False, dest_path: Optional[str]=None) -> Optional[str]:
        """
        Create an immutable snapshot of a file or directory.
        """
        if path and path.startswith('key://'):
            path = self.resolveKeyPath(path)
            if not path:
                print('Unable to resolve key path.', file=sys.stderr)
                return None

        if path.startswith('sha1dir://'):
            # be sure to also snapshot the directory object that would also be needed
            list0 = path.split('/')
            if len(list0) > 3:
                sha1dirpath = '/'.join(list0[:3])
                self.createSnapshot(path=sha1dirpath, upload_to=upload_to,
                                    download_recursive=False, upload_recursive=False, dest_path=None)

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
                location, collection, key, subkey, extra_path = self._parse_key_path(
                    dest_path)
                if not location:
                    raise Exception('Error parsing key path', dest_path)
                if extra_path:
                    raise Exception('Invalid key path for storage', dest_path)
                if location == 'local':
                    if collection != 'default':
                        raise Exception(
                            'Collection must be default for local key path.', collection)
                    collection = None
                elif location == 'pairio':
                    pass
                else:
                    raise Exception('Invalid location for key path', location)

                if not self.setValue(key=key, subkey=subkey, value=address, collection=collection):
                    raise Exception(
                        'Unable to store address in path', dest_path)
            else:
                self.realizeFile(path=address, dest_path=dest_path)

        return address

    @mtlogging.log(name='MountainClient:loadObject')
    def resolveKeyPath(self, key_path: str) -> Optional[str]:
        """
        Resolve keyed file path into its sha1 address.

        Parameters
        ----------
            key_path : str
                Object path with a 'key://' prefix.

        Returns
        -------
        str or None
            Resolved address of an object or None if it could not be resolved.
        """
        if not key_path.startswith('key://'):
            return key_path
        location, collection, key, subkey, extra_path = self._parse_key_path(
            key_path)

        if location == 'local':
            if collection != 'default':
                print('Warning: Invalid key path local collection', collection)
                return None
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

    def _parse_key_path(self, key_path: str) -> Tuple[Optional[str], Optional[str], Optional[str], Optional[str], Optional[str]]:
        list0 = key_path.split('/')
        if len(list0) < 5:
            return (None, None, None, None, None)
        location = list0[2]
        collection = list0[3]
        key = list0[4]
        subkey: Optional[str] = None
        if ':' in key:
            vals0 = key.split(':')
            if len(vals0) != 2:
                return (None, None, None, None, None)
            key = vals0[0]
            subkey = vals0[1]
        extra_path = '/'.join(list0[5:])
        return (location, collection, key, subkey, extra_path)

    def _create_snapshot_helper_save_dd(self, *, basepath: str, dd: dict, upload_to: Optional[StrOrStrList]) -> bool:
        for fname in dd['files'].keys():
            fpath = os.path.join(basepath, fname)
            if not self.saveFile(path=fpath, upload_to=upload_to):
                if not upload_to:
                    print('Unable to copy file to local cache: ' +
                          fpath, file=sys.stderr)
                else:
                    print('Unable to upload file: ' + fpath, file=sys.stderr)
                return False
        for dname, dd0 in dd['dirs'].items():
            dpath = os.path.join(basepath, dname)
            if not self._create_snapshot_helper_save_dd(basepath=dpath, dd=dd0, upload_to=upload_to):
                return False
        return True

    # load text / save text
    @mtlogging.log(name='MountainClient:loadText')
    def loadText(self, *, key: Optional[StrOrDict]=None, path: Optional[str]=None, subkey: Optional[str]=None, local_first: bool=False, collection: Optional[str]=None, download_from: Optional[StrOrStrList]=None, local_only: bool=False, remote_only: bool=False) -> Optional[str]:
        """
        Get content of a specified file, downloading the file from a remote server if needed.
        For detailed info on what you can pass as path or key, see docs for realizeFile().

        Parameters
        ----------
        path : str, optional
            The path of a file to read. This could either be a local path,
            a SHA-1 URL, or a kbucket URL as described in docs for realizeFile().
            One of path or key must be provided
        key : str, optional
            The key used for locating the file as described in docs for realizeFile().
            One of path or key must be provided
        subkey : str, optional
            The optional subkey as described in the docs for getValue() and
            setValue() (the default is None)
        local_first : bool, optional
            In the case where key is used (rather than path), specifies whether
            to consult the local database first, prior to requesting the SHA-1
            hash from the remote collection. (The default is None, meaning that
            only the configured database is used)

        Returns
        -------
        str or None
            Content of downloaded file or None if the file was not found or could
            not be opened.
        """
        if path and path.startswith('key://'):
            path = self.resolveKeyPath(path)
            if not path:
                return None

        fname = self.realizeFile(
            key=key, path=path, subkey=subkey, local_first=local_first, collection=collection, download_from=download_from, local_only=local_only, remote_only=remote_only)
        if fname is None:
            return None
        try:
            with open(fname) as f:
                return f.read()
        except:
            print('Unexpected problem reading file in loadText: ' + fname)
            return None

    @mtlogging.log(name='MountainClient:saveText')
    def saveText(self, text: str, *, key: Optional[StrOrDict]=None, subkey: Optional[str]=None, collection: Optional[str]=None, basename='file.txt', local_also=False, dest_path: Optional[str]=None, upload_to: Optional[StrOrStrList]=None) -> Optional[str]:
        """
        Save given text to a file, put that file in a local SHA-1 cache
        and/or upload to a remote KBucket share. Return SHA-1 URL referring
        to the file.

        Parameters
        ----------
        text : str
        key : str, optional
        subkey : str, optional
        collection : str
        basename : str, optional
        dest_path : str, optional
            Local path to save the file to. If not provided the file will only
            be uploaded to a remote repository without storing a local copy
        upload_to : str, optional
        Returns
        -------
        str or None
            SHA-1 URL referring for the saved or uploaded file or None if the file
            could not be saved.
        """
        if text is None:
            self.setValue(key=key, subkey=subkey,
                          value=None, local_also=local_also, collection=collection)
            return
        if dest_path is None:
            tmp_fname = _create_temporary_file_for_text(text=text)
        else:
            with open(dest_path, 'w') as f:
                f.write(text)
            tmp_fname = dest_path
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
    def readDir(self, path: str, recursive: bool = False, include_sha1: bool = True, download_from: Any = None, local_only: bool = False, remote_only: bool = False) -> Optional[dict]:
        if path and path.startswith('key://'):
            path_resolved: str = self.resolveKeyPath(path)
            if not path_resolved:
                return None
        else:
            path_resolved = path

        if path_resolved.startswith('kbucket://'):
            raise Exception('kbucket:// paths are no longer supported.')

        if path_resolved.startswith('sha1dir://'):
            list0 = path_resolved.split('/')
            sha1 = list0[2]
            if '.' in sha1:
                sha1 = sha1.split('.')[0]
            dd = self.loadObject(path='sha1://' + sha1, download_from=download_from,
                                 local_only=local_only, remote_only=remote_only)
            if not dd:
                return None
            ii = 3
            while ii < len(list0):
                name0 = list0[ii]
                if name0 in dd['dirs']:
                    dd = dd['dirs'][name0]
                else:
                    return None
                ii = ii + 1
            return dd
        else:
            ret = self._read_file_system_dir(
                path=path_resolved, recursive=recursive, include_sha1=include_sha1)
        return ret

    @mtlogging.log(name='MountainClient:computeDirHash')
    def computeDirHash(self, path: str) -> Optional[str]:
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

    def _maybe_resolve(self, path: str) -> str:
        if not path or not path.startswith('key://'):
            return path
        resolved_path = self.resolveKeyPath(path)
        if not resolved_path:
            raise KeyError('{} could not be resolved'.format(path))
        return resolved_path

    @mtlogging.log(name='MountainClient:computeFileSha1')
    def computeFileSha1(self, path: str) -> Optional[str]:
        try:
            path = self._maybe_resolve(path)
            return self._local_db.computeFileSha1(path=path)
        except KeyError:
            return None

    def sha1OfObject(self, obj: dict) -> str:
        return _sha1_of_object(obj)

    @mtlogging.log(name='MountainClient:computeFileOrDirHash')
    def computeFileOrDirHash(self, path: str) -> Optional[str]:
        if path.startswith('kbucket://'):
            raise Exception('kucket:// paths are no longer supported')

        if path and (path.startswith('sha1dir://') or path.startswith('key://')):
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

    def isFile(self, path: str) -> bool:
        if self.isLocalPath(path=path):
            return os.path.isfile(path)

        if path.startswith('kbucket://'):
            raise Exception('kucket:// paths are no longer supported')

        if path.startswith('sha1://'):
            return True
        elif path.startswith('sha1dir://'):
            if len(path.split('/')) <= 3:
                return False
            else:
                return (self.computeFileSha1(path) is not None)
        elif path.startswith('sha1dir://') or path.startswith('key://'):
            return (self.computeFileSha1(path) is not None)
        else:
            return os.path.isfile(path)

    def isLocalPath(self, path: str) -> bool:
        # rename to isLocalFilePath
        if path.startswith('kbucket://'):
            raise Exception('kucket:// paths are no longer supported')

        if path.startswith('sha1://') or path.startswith('sha1dir://') or path.startswith('key://'):
            return False
        return True

    def localCacheDir(self) -> str:
        return self._local_db.localCacheDir()

    def alternateLocalCacheDirs(self) -> List[str]:
        return self._local_db.alternateLocalCacheDirs()

    @mtlogging.log(name='MountainClient:findFileBySha1')
    def findFileBySha1(self, *, sha1: str, download_from: Optional[StrOrStrList]=None, local_only: bool=False) -> Optional[str]:
        return self._realize_file(path='sha1://' + sha1, resolve_locally=False, local_only=local_only, download_from=download_from)

    @mtlogging.log(name='MountainClient:getSha1Url')
    def getSha1Url(self, path: str, *, basename: Optional[str]=None) -> Optional[str]:
        if basename is None:
            basename = os.path.basename(path)

        sha1 = self.computeFileSha1(path)
        if not sha1:
            return None

        return 'sha1://{}/{}'.format(sha1, basename)

    @mtlogging.log(name='MountainClient:findFile')
    def findFile(self, path: str, local_only: bool=False, remote_only: bool=False, download_from: Optional[StrOrStrList]=None) -> Optional[str]:
        if path and path.startswith('key://'):
            path = self.resolveKeyPath(path)
            if not path:
                return None
        return self._realize_file(path=path, resolve_locally=False, local_only=local_only, remote_only=remote_only, download_from=download_from)

    @mtlogging.log(name='MountainClient:copyToLocalCache')
    def copyToLocalCache(self, path: str, basename: Optional[str]=None) -> Optional[str]:
        if path and path.startswith('key://'):
            path = self.resolveKeyPath(path)
            if not path:
                return None
        return self._save_file(path=path, return_sha1_url=False, basename=basename)

    def _initialize_kacheries(self) -> None:
        kacheries_fname = os.path.join(os.environ.get(
            'HOME', ''), '.mountaintools', 'kacheries')
        kachery_upload_tokens_fname = os.path.join(os.environ.get(
            'HOME', ''), '.mountaintools', 'kachery_upload_tokens')
        kachery_urls = dict()
        kachery_upload_tokens: dict = dict()
        kachery_download_tokens: dict = dict()
        if os.path.exists(kacheries_fname):
            txt = _read_text_file(kacheries_fname)
            lines = txt.splitlines()
            for line in lines:
                if (not line.startswith('#')) and (len(line.strip()) > 0):
                    vals = line.strip().split()
                    if len(vals) != 2:
                        print('WARNING: problem parsing kacheries file.')
                    else:
                        kachery_urls[vals[0]] = vals[1]
        if os.path.exists(kachery_upload_tokens_fname):
            txt = _read_text_file(kachery_upload_tokens_fname)
            lines = txt.splitlines()
            for line in lines:
                if (not line.startswith('#')) and (len(line.strip()) > 0):
                    vals = line.strip().split()
                    if len(vals) != 2:
                        print('WARNING: problem parsing kachery_upload_tokens file.')
                    else:
                        kachery_upload_tokens[vals[0]] = vals[1]
        from .kachery_tokens import KacheryTokens
        db = KacheryTokens()
        kachery_upload_tokens = {name: token for name,
                                 type, token in db.entries() if type == 'upload'}
        kachery_download_tokens = {
            name: token for name, type, token in db.entries() if type == 'download'}
        for name, url in kachery_urls.items():
            self._kachery_urls[name] = url
        for name, token in kachery_upload_tokens.items():
            self._kachery_upload_tokens[name] = token
        for name, token in kachery_download_tokens.items():
            self._kachery_download_tokens[name] = token

    def _read_pairio_tokens(self) -> None:
        pairio_tokens_fname = os.path.join(os.environ.get(
            'HOME', ''), '.mountaintools', 'pairio_tokens')
        if os.path.exists(pairio_tokens_fname):
            txt = _read_text_file(pairio_tokens_fname)
            lines = txt.splitlines()
            for line in lines:
                if (not line.startswith('#')) and (len(line.strip()) > 0):
                    vals = line.strip().split()
                    if len(vals) != 2:
                        print('WARNING: problem parsing pairio tokens file.')
                    else:
                        self._pairio_tokens[vals[0]] = vals[1]

    def _get_value(self, *, key: Union[str, dict], subkey: Union[None, str]=None, collection: Union[None, str]=None, local_first: bool=False, check_alt: bool=False) -> Optional[str]:
        if local_first or not collection:
            ret = self._local_db.getValue(
                key=key, subkey=subkey, check_alt=check_alt)
            if ret is not None:
                return ret
        if collection:
            ret = self._remote_client.getValue(
                key=key, subkey=subkey, collection=collection, url=self._pairio_url)
            if ret is not None:
                return ret
        return None

    def _get_value_from_alias(self, alias: str) -> Optional[str]:
        if alias in self._values_by_alias:
            return self._values_by_alias[alias]
        vals = alias.split('.')
        if len(vals) != 2:
            raise Exception('Invalid alias: ' + alias)
        ret = self.getValue(key=vals[1], collection=vals[0])
        if ret is None:
            return None
        self._values_by_alias[alias] = ret
        return ret

    def _set_value(self, *, key: StrOrDict, subkey: Optional[str], value: Union[str, None], overwrite: bool, local_also: bool=False, collection: Optional[str]=None) -> bool:
        if collection:
            token = self._pairio_tokens.get(collection, None)
        else:
            token = None
        if collection and (not token):
            raise Exception('Unable to set value... no token found for collection {}'.format(
                collection))  # should we throw an exception here?
        if local_also or (not collection):
            if not self._local_db.setValue(key=key, subkey=subkey, value=value, overwrite=overwrite):
                return False
        if collection:
            if not self._remote_client.setValue(key=key, subkey=subkey, value=value, overwrite=overwrite, collection=collection, url=self._pairio_url, token=str(token)):
                raise Exception(
                    'Error setting value to remote collection {}'.format(collection))
        return True

    def _get_sub_keys(self, *, key: Union[str, dict], collection: Union[str, None]) -> Optional[List[str]]:
        if collection:
            return self._remote_client.getSubKeys(key=key, collection=collection, url=self._pairio_url)
        else:
            return self._local_db.getSubKeys(key=key)

    def _realize_file(self, *, path: str, resolve_locally: bool=True, local_only: bool=False, remote_only: bool=False, dest_path: Optional[str]=None, show_progress: bool=False, download_from: Optional[StrOrStrList]=None) -> Optional[str]:
        if not remote_only:
            ret = self._local_db.realizeFile(
                path=path, local_only=local_only, resolve_locally=resolve_locally, dest_path=dest_path, show_progress=show_progress)
            if ret:
                return ret
        if local_only:
            return None
        if path.startswith('sha1dir://'):
            sha1 = self.computeFileSha1(path)
            if not sha1:
                return None
            path = 'sha1://' + sha1
            # the proceed
        download_froms: List[str] = []
        if download_from is not None:
            if type(download_from) == str:
                download_froms.append(str(download_from))
            else:
                download_froms.extend(download_from)
        for kname in self._config_download_from:
            download_froms.append(kname)
        if path.startswith('sha1://'):
            list0 = path.split('/')
            sha1 = list0[2]
            for df0 in download_froms:
                url, size = self._find_on_kachery_or_kbucket(
                    download_from=df0, sha1=sha1)
                if url and (size is not None):
                    if resolve_locally:
                        return self._local_db.realizeFileFromUrl(url=url, sha1=sha1, size=size, dest_path=dest_path, show_progress=show_progress)
                    else:
                        return url
        return None

    @mtlogging.log()
    def _save_file(self, *, path: str, basename: Optional[str], return_sha1_url: bool=True, upload_to: Optional[StrOrStrList]=None) -> Optional[str]:
        path = self.realizeFile(path)
        if not path:
            return None
        ret = self._local_db.saveFile(
            path=path, basename=basename, return_sha1_url=return_sha1_url)
        if not ret:
            return None
        if upload_to:
            if type(upload_to) == str:
                upload_to = [str(upload_to)]
            for ut in upload_to:
                sha1 = self.computeFileSha1(path=ret)
                kachery_url = self._resolve_kachery_url(ut)
                if not kachery_url:
                    raise Exception(
                        'Unable to resolve kachery url for: {}'.format(ut))
                if ut not in self._kachery_upload_tokens.keys():
                    raise Exception(
                        'Kachery upload token not found for: {}'.format(ut))
                kachery_upload_token = self._kachery_upload_tokens[ut]
                self._upload_to_kachery(
                    path=path, sha1=sha1, kachery_url=kachery_url, upload_token=kachery_upload_token)
        return ret

    def _resolve_kachery_url(self, name: str) -> Optional[str]:
        if name.startswith('http://') or name.startswith('https://'):
            return name
        if '.' in name:
            return self._get_value_from_alias(name)
        if name not in self._kachery_urls.keys():
            return None
        return self._kachery_urls[name]

    def _upload_to_kachery(self, *, path: str, sha1: str, kachery_url: str, upload_token: Optional[str]) -> bool:
        url_check_path0 = '/check/sha1/' + sha1
        url_check = kachery_url + url_check_path0
        resp_obj = _http_get_json(url_check, verbose=self._verbose)
        if not resp_obj['success']:
            print('Warning: Problem checking for upload: ' + resp_obj['error'])
            return False

        if not resp_obj['found']:
            url_path0 = '/set/sha1/' + sha1
            signature = _sha1_of_object(
                {'path': url_path0, 'token': upload_token})
            url = kachery_url + url_path0 + '?signature=' + signature
            size0 = os.path.getsize(path)
            if size0 > 10000:
                print(
                    'Uploading to kachery --- ({}): {} -> {}'.format(_format_file_size(size0), path, url))

            timer = time.time()
            resp_obj = _http_post_file_data(url, path)
            elapsed = time.time() - timer

            if size0 > 10000:
                print('File uploaded ({}) in {} sec'.format(
                    _format_file_size(size0), elapsed))

            if not resp_obj.get('success', False):
                print('Problem posting file data: ' + resp_obj.get('error', ''))
                return False
            return True
        else:
            # print('Already on server (***)')
            return True

    def _find_on_kachery_or_kbucket(self, *, download_from: str, sha1: str) -> Tuple[Optional[str], Optional[int]]:
        kachery_url = self._resolve_kachery_url(download_from)

        if kachery_url:
            check_url = kachery_url + '/check/sha1/' + sha1
            try:
                obj = _http_get_json(check_url, verbose=self._verbose)
            except:
                traceback.print_exc()
                print('WARNING: failed in check to kachery {}: {}'.format(
                    download_from, check_url))
                return (None, None)
            if not obj['success']:
                print('WARNING: problem checking kachery {}: {}'.format(
                    download_from, check_url))
                return (None, None)
            if not obj['found']:
                return (None, None)
            url0 = kachery_url + '/get/sha1/' + sha1
            if download_from in self._kachery_download_tokens:
                download_token0 = self._kachery_download_tokens[download_from]
                url_path0 = '/get/sha1/' + sha1
                signature0 = _sha1_of_object(
                    {'path': url_path0, 'token': download_token0})
                url0 = url0 + '?signature=' + signature0
            return (url0, obj['size'])

        return (None, None)

    def _read_file_system_dir(self, *, path: str, recursive: bool, include_sha1: bool) -> Optional[dict]:
        ret: dict = dict(
            files={},
            dirs={}
        )
        list0 = _safe_list_dir(path)
        if list0 is None:
            return None
        for name0 in list0:
            path0 = path + '/' + name0
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


@mtlogging.log()
def _http_post_file_data(url: str, fname: str, verbose: Optional[bool]=None) -> Any:
    timer = time.time()
    if verbose is None:
        verbose = (os.environ.get('HTTP_VERBOSE', '') == 'TRUE')
    if verbose:
        print('_http_post_file_data::: ' + fname)
    with open(fname, 'rb') as f:
        try:
            obj = requests.post(url, data=f)
        except:
            raise Exception('Error posting file data.')
    if obj.status_code != 200:
        raise Exception('Error posting file data: {} {}'.format(
            obj.status_code, obj.content.decode('utf-8')))
    if verbose:
        print('Elapsed time for _http_post_file_Data: {}'.format(time.time() - timer))
    return json.loads(obj.content)


# thanks: https://stackoverflow.com/questions/1094841/reusable-library-to-get-human-readable-version-of-file-size


def _format_file_size(size: Optional[int]) -> str:
    if not size:
        return 'Unknown'
    if size <= 1024:
        return '{} B'.format(size)
    return _sizeof_fmt(size)


def _sizeof_fmt(num: float, suffix: str='B') -> str:
    for unit in ['', 'Ki', 'Mi', 'Gi', 'Ti', 'Pi', 'Ei', 'Zi']:
        if abs(num) < 1024.0:
            return "%3.1f %s%s" % (num, unit, suffix)
        num /= 1024.0
    return "%.1f %s%s" % (num, 'Yi', suffix)


def _create_temporary_file_for_text(*, text: str) -> str:
    tmp_fname = _create_temporary_fname('.txt')
    with open(tmp_fname, 'w') as f:
        f.write(text)
    return tmp_fname


def _safe_list_dir(path: str) -> Optional[List[str]]:
    try:
        ret = os.listdir(path)
        return ret
    except:
        return None


# The global module client
_global_client = MountainClient()
client = _global_client
