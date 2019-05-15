# pairioserver

## To run via docker:

```
docker run -it --net=host magland/pairioserver [admin_token] [mongodb_url] [port]
```

For example:

```
docker run -it --net=host magland/pairioserver test_admin_token mongodb://localhost:27017 20001
```

## To test a running server:

First make sure pairio python module is available. You can do this by installing spikeforest2 or by running

```
cd mountaintools
python setup.py develop
```

Then, from python run the following test:

```
from mountaintools import client as ca

# Create a collection on server with a test token
ca.setRemoteConfig(url='http://localhost:20001')
ca.addRemoteCollection(collection='test_collection1',token='test_token1',admin_token='test_admin_token')

# Configure to point to the new collection
ca.setRemoteConfig(url='http://localhost:20001',collection='test_collection1',token='test_token1')

# Test setting/getting
ca.setValue(key='test_key1',value='test_value1')
assert ca.getValue(key='test_key1')=='test_value1'
print('okay!')
```

## To build and push the docker image:

```
docker build -t magland/pairioserver .
docker push magland/pairioserver
```

