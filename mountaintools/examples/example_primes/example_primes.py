#%%
# Import the MountainTools client and connect to a remote database
from mountaintools import client as mt
mt.configRemoteReadonly(collection='spikeforest', share_id='spikeforest.spikeforest2')

# Optionally configure write access to database (authorization required)
write_to_server=False
if write_to_server:
    mt.login()
    mt.configRemoteReadWrite(collection='spikeforest', share_id='spikeforest.spikeforest2')

#%%
# Other imports
import numpy as np
import mlprocessors as mlpr

# Compute the first n primes
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


# MountainTools processor wrapper for compute_n_primes()
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
# Execute the processor (retrieve from cache if already computed)
ComputeNPrimes.execute(n=int(1e5), output='primes.npy')

# save to database if logged in
mt.saveFile('primes.npy')

# Load the output into a numpy array and print
primes=np.load('primes.npy')
print(primes)

#%%
# Plot the number of primes vs the predicted based on the prime number theorem
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
