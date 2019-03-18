from mountaintools import client as mt
import json
import subprocess
import sys
import pytest
import time
import os
import signal
import tempfile


def test_cairio(tmpdir):
    tmpdir = str(tmpdir)
    os.environ['KBUCKET_CACHE_DIR'] = tmpdir+'/sha1-cache'

    from mountaintools import CairioClient
    cc = CairioClient()

    # Setting values (these should be short strings, <=80 characters)
    cc.setValue(key=dict(name='some-key1'), value='hello 1')
    cc.setValue(key=dict(name='some_name', number=2), value='hello 2')

    # Getting values
    val1 = cc.getValue(key=dict(name='some-key1'))
    val2 = cc.getValue(key=dict(name='some_name', number=2))

    assert val1 == 'hello 1'
    assert val2 == 'hello 2'

    # Local storage of data and files, retrievable by SHA-1 hash
    some_text = 'This is some text'
    path = cc.saveText(some_text, basename='test.txt')
    print(path)
    # Output: sha1://482cb0cfcbed6740a2bcb659c9ccc22a4d27b369/test.txt

    # Later we can use this to retrieve the text
    assert cc.loadText(path=path) == some_text

    # ... or retrieve the path to a local file containing the text
    fname = cc.realizeFile(path)
    assert type(fname) == str
    print(fname)
    # Output: /tmp/sha1-cache/4/82/482cb0cfcbed6740a2bcb659c9ccc22a4d27b369

    # Or we can store some large text by key and retrieve it later
    large_text = 'some large repeating text'*100
    cc.saveText(key=dict(name='key-for-repeating-text'), text=large_text)
    txt = cc.loadText(key=dict(name='key-for-repeating-text'))
    assert txt == large_text

    # Similarly we can store python dicts via json content
    some_object = dict(some='object')
    path = cc.saveObject(some_object, basename='object.json')
    print(path)
    # Output: sha1://b77fdda467b03d7a0c3e06f6f441f689ac46e817/object.json

    retrieved_object = cc.loadObject(path=path)
    print(retrieved_object)
    assert json.dumps(retrieved_object) == json.dumps(some_object)

    # Or store objects by key
    some_other_object = dict(some_other='object')
    cc.saveObject(object=some_other_object, key=dict(some='key'))
    obj = cc.loadObject(key=dict(some='key'))
    assert json.dumps(some_other_object) == json.dumps(obj)

    # You can do the same with files
    with open(tempfile.gettempdir()+'/test___.txt', 'w') as f:
        f.write('some file content')
    path = cc.saveFile(tempfile.gettempdir()+'/test___.txt')
    print(path)
    # Output: sha1://ee025361a15e3e8074e9c0b44b4f98aabc829b3d/test___.txt

    # Then load the text of the file at a later time
    txt = cc.loadText(path=path)
    print(txt)
    assert txt == 'some file content'

    sha1 = cc.computeFileSha1(path=cc.realizeFile(path))
    txt2 = cc.loadText(path='sha1://'+sha1)
    assert txt2 == 'some file content'


def test_cairio_subkeys():
    from mountaintools import CairioClient
    cc = CairioClient()

    # data for the first pass
    subkeys = ['key1', 'key2', 'key3']
    subvals = ['val1-', 'val2-', 'val3-']
    for pass0 in range(1, 3):  # two passes
        cc.setValue(key='parent_key', subkey='-', value=None)  # clear it out
        for sk, sv in zip(subkeys, subvals):
            cc.setValue(key='parent_key', subkey=sk, value=sv)
        for sk, sv in zip(subkeys, subvals):
            val0 = cc.getValue(key='parent_key', subkey=sk)
            assert val0 == sv
        tmp = cc.getSubKeys(key='parent_key')
        assert set(tmp) == set(subkeys)
        # data for the second pass
        subkeys = ['key1']
        subvals = ['val1b']


@pytest.fixture
def cairioserver(request):
    port = 20010
    cmd = 'CAIRIO_ADMIN_TOKEN=test_admin_token PORT={} node /home/project/mountaintools/cairioserver/cairioserver/cairioserver.js'.format(
        port)
    popen = subprocess.Popen(cmd, stdout=sys.stdout,
                             universal_newlines=True, shell=True)

    def finalize():
        print('Terminating cairio server...')
        os.killpg(os.getpgid(popen.pid), signal.SIGTERM)
    request.addfinalizer(finalize)
    return dict(
        url='http://localhost:{}'.format(port)
    )


@pytest.mark.exclude
@pytest.mark.cairioserver
def test_cairioserver(cairioserver):
    print('test_cairioserver')
    time.sleep(2)

    from mountaintools import CairioClient
    cc = CairioClient()
    cc.setRemoteConfig(url=cairioserver['url'])
    cc.addRemoteCollection(collection='test_collection1',
                           token='test_token1', admin_token='test_admin_token')

    # Configure to point to the new collection
    cc.setRemoteConfig(
        url=cairioserver['url'], collection='test_collection1', token='test_token1')

    # Test setting/getting
    cc.setValue(key='test_key1', value='test_value1')
    assert cc.getValue(key='test_key1') == 'test_value1'
    print('okay!')
