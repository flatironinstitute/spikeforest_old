#%% python magic
#get_ipython().run_line_magic('load_ext', 'autoreload')
#get_ipython().run_line_magic('autoreload', '2')

#%%
from mountaintools import client as mt
mt.configRemoteReadonly(collection='spikeforest', share_id='69432e9201d0')

write_to_server=False
if write_to_server:
    mt.login()
    mt.configRemoteReadWrite(collection='spikeforest', share_id='69432e9201d0')

#%%
import numpy as np
import mlprocessors as mlpr

def compute_n_primes(n):
    prime_list = [2]
    num = 3
    while len(prime_list) < n:
        for p in prime_list:  # TODO: we only need to check up to the square root of the number
            if num % p == 0:
                break
        else:
            prime_list.append(num)
        num += 2
    return np.array(prime_list)


class ComputeNPrimes(mlpr.Processor):
    NAME = 'ComputeNPrimes'
    VERSION = '0.1.3'

    n = mlpr.IntegerParameter('The integer n.')
    output = mlpr.Output('The output .npy file.')

    def __init__(self):
        mlpr.Processor.__init__(self)

    def run(self):
        primes = compute_n_primes(self.n)
        print('Prime {}: {}'.format(self.n, primes[-1]))
        np.save(self.output,primes)
        

#%%
ComputeNPrimes.execute(n=int(1e5), output='primes.npy')
mt.saveFile('primes.npy')

primes=np.load('primes.npy')
print(primes)

#%%
from matplotlib import pyplot as plt

N=len(primes)
primes_N=primes[0:N]

nn=np.arange(1,N+1)
plt.plot(primes_N,primes_N/np.log(primes_N),'r',primes_N,nn,'b')
plt.xlabel('The integer n')
plt.ylabel('Number of primes less than n')
plt.legend(['Predicted', 'Computed'])
plt.title('Actual and predicted number of primes')
plt.show()



#%%
