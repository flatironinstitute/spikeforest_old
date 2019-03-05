import numpy as np
import mlprocessors as mlpr

def nth_prime_number(n):
    prime_list = [2]
    num = 3
    while len(prime_list) < n:
        for p in prime_list:  # TODO: we only need to check up to the square root of the number
            if num % p == 0:
                break
        else:
            prime_list.append(num)
        num += 2
    return prime_list[n-1]


class ComputeNthPrime(mlpr.Processor):
    NAME = 'ComputeNthPrime'
    VERSION = '0.1.1'

    n = mlpr.IntegerParameter('The integer n.')
    output = mlpr.Output('The output text file.')

    def __init__(self):
        mlpr.Processor.__init__(self)

    def run(self):
        # if self.n==10010:
        #     raise Exception('Test exception, n={}'.format(self.n))
        prime = nth_prime_number(self.n)
        print('Prime {}: {}'.format(self.n, prime))
        with open(self.output, 'w') as f:
            f.write('{}'.format(prime))