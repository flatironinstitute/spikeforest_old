# mountainclient

MountainClient is a Python client for loading, saving, downloading, and uploading files
referenced by MountainTools paths and an interface to remote pairio and
kachery databases, a local key/value store, and a local SHA-1 file cache.
All I/O for MountainTools is handled using this client.

There is a global client that may be imported via

```python
    from mountaintools import client as mt
```

Or you can instantiate a local client object:

```python
    from mountaintools import MountainClient
    mt_client = MountainClient()
```

The global client allows a single configuration to apply to the entire
program, but there are also times when using a local instance is preferred.

By default the client utilizes databases stored in directories on your local
disk, but it can also be used to read and write from remote servers. For
example, the following code saves and retrieves some short text strings
using the local file system as storage.

```python
    from mountaintools import client as mt

    # Setting values (these should be short strings, <=80 characters)
    mt.setValue(key='some-key1', value='hello 1')
    mt.setValue(key=dict(name='some_name', number=2), value='hello 2')

    # Getting values
    val1 = mt.getValue(key='some-key1')
    val2 = mt.getValue(key=dict(name='some_name', number=2))
```

By default these are stored inside the `~/.mountain` database directory. This
location may be configured using the `MOUNTAIN_DIR` environment variable.

While `setValue()` and `getValue()` are limited to working with short strings,
larger objects may be stored using saveText(), saveObject() and saveFile(),
and retrieved using `loadText()`, `loadObject()` and `loadFile()`, as follows:

```python
    from mountaintools import client as mt

    # Local storage of data and files, retrievable by SHA-1 hash
    some_text = 'This is some text'
    path = mt.saveText(some_text, basename='test.txt')
    print(path)
    # Output: sha1://482cb0cfcbed6740a2bcb659c9ccc22a4d27b369/test.txt

    # Later we can use this to retrieve the text
    retrieved_text = mt.loadText(path='sha1://482cb0cfcbed6740a2bcb659c9ccc22a4d27b369/test.txt')

    # ... or retrieve the path to a local file containing the text
    fname = mt.realizeFile(path)
    print(fname)
    # Output: /tmp/sha1-cache/4/82/482cb0cfcbed6740a2bcb659c9ccc22a4d27b369

    # Or we can store some large text by key and retrieve it later
    large_text = 'some large repeating text'*100
    mt.saveText(key=dict(name='key-for-repeating-text'), text=large_text)
    txt = mt.loadText(key=dict(name='key-for-repeating-text'))

    # Similarly we can store simple Python dicts via json content
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
```

The larger content is stored in a disk-backed content-addressable storage
database, located by default at `/tmp/sha1-cache`. This may be configured by
setting the `SHA1_CACHE_DIR` environment variable.


### Setting kachery tokens
For interacting with kachery servers it is required that mountaintools knows about access tokens to upload or download files.
For that you need to put the tokens into `~/.mountaintools/kachery_tokens` file.

This file is a text file with three column records in each row.
Each record consists of a server name or URL, token type (currently `upload` or `download`) and finally token contents.

You can modify this file by hand but it is suggested that you rather use `kachery-token` which comes with mountaintools.
To add a token run a command similar to `kachery-token add companylab.spike download ***tokendata***` replacing `***tokendata***` with the actual token.

You can list registered tokens with `kachery-token list`. 

```
companylab.spike    download    l***5
http://127.0.0.1    upload      p***w
```

The tool will mask away token data. To unmask it run the tool with `--show-tokens` option.

```
companylab.spike    download    l51umhmqjp35
http://127.0.0.1    upload      pnu8oyw6oyjw
```


## Commandline tools

Mountaintools comes with a set of commands that can be invoked from a terminal.
Their aim is to provide a quick way to perform common tasks of manipulating objects stored in remote mountain databases.

### mt-cat
Writes contents of a local or remote file to stdout.

```bash
mt-cat [-h] [--download-from DOWNLOAD_FROM] path
```

This is a very simplified equivalent of `cat` where you can pass in a compatible mountaintools URI path and it will try to locate the given file and retrieve it if available and then print its contents to standard output.

You can optionally pass in `--download-from` option together with a name of a server where you expect to find the file.

### mt-download
Retrieves a file and places it in a given destination path.
```bash
mt-download [-h] [--verbose] [--download-from DOWNLOAD_FROM] src_path dst_path
```

This tool can be treated as an equivalent of `cp` command. `src_path` should be a mountaintools URI pointing to a file or directory and `dst_path` should be a path in your filesystem where to place retrieved data.

You can optionally pass in `--download-from` option together with a name of a server where you expect to find the file.

### mt-find
This tool finds the given file and prints its location.

```bash
mt-find [-h] [--verbose] [--local-only] [--remote-only] [--download-from DOWNLOAD_FROM] path
```

By default it searches both local and remote locations but it can be restricted using `--local-only`
or `--remote-only` switches.

If the file is found, its local path is printed to standard output. If the entity represents a directory
then that information is printed instead of the path.

### mt-ls
This tool lists the contents of a local or remote directory expressed as a `sha1dir://` address.

```bash
usage: mt-ls [-h] [--download-from DOWNLOAD_FROM] path

List the contents of a remote database directory

positional arguments:
  path                  Local or remote path (sha1dir://...)

optional arguments:
  -h, --help            show this help message and exit
  --download-from DOWNLOAD_FROM
```


### mt-resolve-key-path
This tool resolves a key:// entry into a real (local or remote) path.

```bash
usage: mt-resolve-key-path [-h] key_path

Display the resolved path associated with a key://... path.

positional arguments:
  key_path    Path to local file or directory

optional arguments:
  -h, --help  show this help message and exit
```

### mt-snapshot

Compute the hash of a local or remote file or directory and print the address representing a snapshot.
```
usage: mt-snapshot [-h] [--upload-to UPLOAD_TO] [--download-recursive]
                   [--upload-recursive] [--login]
                   path [dest_path]

Compute the hash of a local or remote file or directory and print the 
address representing a snapshot.

positional arguments:
  path                  Path to local file or directory
  dest_path             Optional destination key path

optional arguments:
  -h, --help            show this help message and exit
  --upload-to UPLOAD_TO, -u UPLOAD_TO
                        Remote database to upload all files
  --download-recursive, --dr
                        Download all remote files to the local SHA-1 cache.
  --upload-recursive, --ur
                        Upload all files (recursively).
  --login               Whether to log in
```

After the snapshot is computed, the file can optionally be uploaded to one or more servers (defined with `--upload-to`).

