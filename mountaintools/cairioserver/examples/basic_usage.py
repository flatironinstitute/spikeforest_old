from mountaintools import client as ca

print('------------------------------------------------')

# Local key/value store for associating relatively short strings (<=80 characters) with arbitrary keys (strings or dicts)

# Setting values (these should be short strings, <=80 characters)
ca.setValue(key='some-key1', value='hello 1')
ca.setValue(key=dict(name='some_name', number=2), value='hello 2')

# Getting values
val1 = ca.getValue(key='some-key1')
val2 = ca.getValue(key=dict(name='some_name', number=2))
print(val1)
print(val2)

print('------------------------------------------------')

# Setting password-protected values
ca.setValue(key='some_key2', password='my_password', value='the-secret-*y$#a')

# Retrieving password-protected values
print(ca.getValue(key='some_key2', password='my_password'))

print('------------------------------------------------')

# Local storage of data and files, retrievable by SHA-1 hash

path = ca.saveText('This is some text', basename='test.txt')
print(path)
# Output: sha1://482cb0cfcbed6740a2bcb659c9ccc22a4d27b369/test.txt

# Later we can use this to retrieve the text
txt = ca.loadText(path=path)
print(txt)

# ... or retrieve the path to a local file containing the text
fname = ca.realizeFile(path=path)
print(fname)
# Output: /tmp/sha1-cache/4/82/482cb0cfcbed6740a2bcb659c9ccc22a4d27b369

# Or we can store some large text by key and retrieve it later
ca.saveText(key=dict(name='key-for-repeating-text'),
            text='some large repeating text'*100)
txt = ca.loadText(key=dict(name='key-for-repeating-text'))
print(len(txt))  # Output: 2500

print('------------------------------------------------')

# Similarly we can store python dicts via json content
path = ca.saveObject(dict(some='object'), basename='object.json')
print(path)
# Output: sha1://b77fdda467b03d7a0c3e06f6f441f689ac46e817/object.json

retrieved_object = ca.loadObject(path=path)
print(retrieved_object)

# Or store objects by key
ca.saveObject(object=dict(some_other='object'), key=dict(some='key'))
obj = ca.loadObject(key=dict(some='key'))
print(obj)

print('------------------------------------------------')

# You can do the same with files
with open('test___.txt', 'w') as f:
    f.write('some file content')
path = ca.saveFile('test___.txt')
print(path)
# Output: sha1://ee025361a15e3e8074e9c0b44b4f98aabc829b3d/test___.txt

# Then load the text of the file at a later time
txt = ca.loadText(path=path)
print(txt)

# REMOTE DATABASE

# The interesting part comes when we connect to a remote cairio database
