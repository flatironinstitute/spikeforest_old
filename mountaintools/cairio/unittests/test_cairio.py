from cairio import client as ca
import json
import subprocess


def test_cairio():
    # Setting values (these should be short strings, <=80 characters)
    ca.setValue(key=dict(name='some-key1'), value='hello 1')
    ca.setValue(key=dict(name='some_name', number=2), value='hello 2')

    # Getting values
    val1 = ca.getValue(key=dict(name='some-key1'))
    val2 = ca.getValue(key=dict(name='some_name', number=2))

    assert val1 == 'hello 1'
    assert val2 == 'hello 2'

    # Setting password-protected values
    secret_value = 'the-secret-*y$#a'
    ca.setValue(key=dict(name='some_secret_token'),
                password='my_password', value=secret_value)

    # Retrieving password-protected values
    assert ca.getValue(key=dict(name='some_secret_token'),
                       password='my_password') == secret_value

    # Local storage of data and files, retrievable by SHA-1 hash
    some_text = 'This is some text'
    path = ca.saveText(some_text, basename='test.txt')
    print(path)
    # Output: sha1://482cb0cfcbed6740a2bcb659c9ccc22a4d27b369/test.txt

    # Later we can use this to retrieve the text
    assert ca.loadText(path=path) == some_text

    # ... or retrieve the path to a local file containing the text
    fname = ca.realizeFile(path)
    assert type(fname) == str
    print(fname)
    # Output: /tmp/sha1-cache/4/82/482cb0cfcbed6740a2bcb659c9ccc22a4d27b369

    # Or we can store some large text by key and retrieve it later
    large_text = 'some large repeating text'*100
    ca.saveText(key=dict(name='key-for-repeating-text'), text=large_text)
    txt = ca.loadText(key=dict(name='key-for-repeating-text'))
    assert txt == large_text

    # Similarly we can store python dicts via json content
    some_object = dict(some='object')
    path = ca.saveObject(some_object, basename='object.json')
    print(path)
    # Output: sha1://b77fdda467b03d7a0c3e06f6f441f689ac46e817/object.json

    retrieved_object = ca.loadObject(path=path)
    print(retrieved_object)
    assert json.dumps(retrieved_object) == json.dumps(some_object)

    # Or store objects by key
    some_other_object = dict(some_other='object')
    ca.saveObject(object=some_other_object, key=dict(some='key'))
    obj = ca.loadObject(key=dict(some='key'))
    assert json.dumps(some_other_object) == json.dumps(obj)

    # You can do the same with files
    with open('test___.txt', 'w') as f:
        f.write('some file content')
    path = ca.saveFile('test___.txt')
    print(path)
    # Output: sha1://ee025361a15e3e8074e9c0b44b4f98aabc829b3d/test___.txt

    # Then load the text of the file at a later time
    txt = ca.loadText(path=path)
    print(txt)
    assert txt == 'some file content'

    sha1 = ca.computeFileSha1(path=ca.realizeFile(path))
    txt2 = ca.loadText(path='sha1://'+sha1)
    assert txt2 == 'some file content'


def test_cairio_subkeys():
    # data for the first pass
    subkeys = ['key1', 'key2', 'key3']
    subvals = ['val1-', 'val2-', 'val3-']
    for pass0 in range(1, 3):  # two passes
        ca.setValue(key='parent_key', subkey='-', value=None)  # clear it out
        for sk, sv in zip(subkeys, subvals):
            ca.setValue(key='parent_key', subkey=sk, value=sv)
        for sk, sv in zip(subkeys, subvals):
            val0 = ca.getValue(key='parent_key', subkey=sk)
            assert val0 == sv
        tmp = ca.getSubKeys(key='parent_key')
        assert set(tmp) == set(subkeys)
        # data for the second pass
        subkeys = ['key1']
        subvals = ['val1b']

# @pytest.fixture
# def cairioserver(request):
#     cmd='node /home/project/mountaintools/cairioserver/cairioserver/cairioserver.js'
#     popen = subprocess.Popen(cmd, stdout=subprocess.PIPE, universal_newlines=True, shell=True)
#     request.addfinalizer(lambda: popen.kill())
#     return popen
