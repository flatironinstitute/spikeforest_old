from mountaintools import client as mt
import multiprocessing

# key=dict(test='key')
# for ii in range(20):
#     val0='{}'.format(ii)
#     mt.setValue(key=key,value=val0)
#     val1=mt.getValue(key=key)
#     print(val0,val1)
#     assert val0==val1

# for ii in range(20):
#     subkey='{}'.format(ii)
#     val0='{}'.format(ii)
#     mt.setValue(key=key,subkey=subkey,value=val0)
#     val1=mt.getValue(key=key,subkey=subkey)
#     print(val0,val1)
#     assert val0==val1

def _test1(ii):
    key=dict(test='key3')
    val0='{}'.format(ii)
    mt.setValue(key=key,value=val0)
    val1=mt.getValue(key=key)
    print(val0,'------',val1)
    return val1

pool=multiprocessing.Pool(100)
pool.map(_test1,[ii for ii in range(100)])
pool.close()
pool.join()