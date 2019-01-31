#!/usr/bin/env python

from pairio import client as pa

pa.setConfig(
    url='http://localhost:11001',
    collections=['magland'],
    user='magland',
    token='6220c9dae511',
    read_local=False,write_local=False,
    read_remote=True,write_remote=True,
    verbose=True
)

expected_val='test-value-803'

pa.set(key='test-key',value=expected_val)
val=pa.get(key='test-key')
print('VALUE: {}    EXPECTED: {}'.format(val,expected_val))
