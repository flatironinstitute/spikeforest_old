# mountainclient

MountainClient is a python client for accessing local and remote mountain
databases and KBucket shares. All I/O for MountainTools is handled using
this client.

There is a global client that may be imported via

```
    from mountaintools import client as mt
```

Or you can instantiate a local client object:

```
    from mountaintools import MountainClient
    mt_client = MountainClient()
```

The global client allows a single login to apply to the entire program, but
there are also times when using a local instance is preferred.

By default the client utilizes cache directories on your local disk, but it
can also be configured to read and write from remote servers. For example,
the following code saves and retrieves some short text strings using the
local file system as storage.

```
    from mountaintools import client as mt

    # Setting values (these should be short strings, <=80 characters)
    mt.setValue(key='some-key1', value='hello 1')
    mt.setValue(key=dict(name='some_name', number=2), value='hello 2')

    # Getting values
    val1 = mt.getValue(key='some-key1')
    val2 = mt.getValue(key=dict(name='some_name', number=2))
```

By default these are stored inside the `~/.mountain` database directory. This
may be configured using the `MOUNTAIN_DIR` environment variable.

While `setValue()` and `getValue()` are limited to working with short strings,
larger objects may be stored using saveText(), saveObject() and saveFile(),
and retrieved using `loadText()`, `loadObject()` and `loadFile()`, as follows:

```
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
```

The larger content is stored in a disk-backed content-addressable storage
database, located by default at `/tmp/sha1-cache`. This may be configured by
setting the `KBUCKET_CACHE_DIR` environment variable.

To access content on a remote server, you can use

```
    from mountaintools import client as mt

    mt.configRemoteReadonly(collection='<collection>', share_id='<id>')
```

where `<collection>` and `<id>` refer to a remote mountain collection and
KBucket share ID. For read/write access you will need to either provide
the authorization tokens or log in as follows:

```
    from mountaintools import client as mt

    mt.login()
    mt.configRemoteReadWrite(collection='<collection>', share_id='<id>')
```
