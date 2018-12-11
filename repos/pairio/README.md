# pairio

Pairio is a system for associating hashes of inputs (keys) with hashes of outputs (values) so that results of processing pipelines may be cached both locally and on the cloud. Essentially it is a key/value store where the keys and values are meant to be 40-character SHA-1 hashes of objects or files.

## Installation of the python client

```
pip install pairio
```

or to install from source clone the repository and then run:

```
python setup.py install
```

or for a development installation, clone the repository and then run:

```
python setup.py develop
```

## Basic usage on local machine

To use pairio on the local computer, simply run

```
from pairio import client as pa
key='some-string-40-or-fewer-characters'
val='another-string-40-or-fewer-characters'
pa.set(key,val)
```

Then later retrieve the value

```
val=pa.get(key)
print(val)
```

Often the key will not be a string, but will instead be a python dict. For example

```
pa.set({'operation':'add','arg1':12,'arg2':30},'42')
```

In this case pairio will use the hash of the JSON string of the key to store the value. Thus the result of this operation could be retrieved later by passing in the same dict key:

```
result=pa.get({'operation':'add','arg1':12,'arg2':30})
print(result)
```

On primary use case is when the value is the SHA-1 hash of a file. For example

```
pa.set({'operation':'bash-stdout','script':'echo "Hello, pairio."'},'a09fd13fd92800aeafe475e9113efe216788d934')
```

Here, the value is the SHA-1 hash of the file whose contents is "Hello, pairio."

## Looking up values in the cloud

Values can be retrieved from the cloud by configuring pairio to look for pairs stored under pairio user accounts. For example, to retrieve the value associated with the dict `{'name':'test'}` in the 'magland' cloud collection, do

```
val=pa.get({'name':'test'},user='magland',local=False)
print(val)
```

If found, you might see the "a-test-string", depending on what is actually in the database. If not found, you will see `None`.

This can also be achieved by configuring pairio to always look for key/value pairs under the 'magland' cloud collection

```
pa.setConfig(collections=['magland'])
val=pa.get({'name':'test'},local=False)
print(val)
```

In general, pairio will first look on the local machine. If they key is not found, it will then look in the cloud under the collection specified as trusted using the `pa.setConfig(collections=collections)` command. If still not found, it will return `None`.

## Storing pairs in the cloud

In order to store key/value pairs in the cloud, you must have a pairio account for some pairio server. Contact the authors if you would like an account on the default pairio server at pairio.org. Once you have a user name and token, you can configure pairio to save key/value pairs in your cloud collection as follows:

```
pa.setConfig(user='your-user-name',token='your-pairio-token')
```

Alternatively, you can set the `PAIRIO_USER` and `PAIRIO_TOKEN` environment variables.

Then subsequent calls to `pa.set()` will set the key/value pairs to both the local machine and to the remote cloud collection associated with your user name.

## Configuration options

You can specify the default behavior of the `pa.get()` and `pa.set()` operations as follows:

```
pa.setConfig(
  collections=['list','of','user','names'], # Names of cloud collections to search when getting values
  user='user-name', # The user name for setting key/value pairs in the cloud
  token='user-token', # The token corresponding to the user name
  local=True, # Whether or not to store key/value pairs locally when set() is called
  remote=True, # Whether or not to store key/value pairs remotely when set() is called
  url='url-to-pairio-server' # Specify a remote pairio server. By default it will point to the server at pairio.org
)
```

## Hosting a pairio server

You can host your own pairio server using npm, for example.
```
npm install
PORT=8888 npm run server
```
The source code for the NodeJS server is found in the `pairioserver/` directory.

To use this server from a pairo client you need to set the `PAIRIO_URL` environment variable.

See server API docs at the top of this file: https://github.com/magland/pairio/blob/master/pairioserver/pairioserver.js

