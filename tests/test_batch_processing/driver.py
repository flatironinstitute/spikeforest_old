#!/usr/bin/env python

import mlprocessors as mlpr
from cairio import client as ca
import numpy as np
import argparse
import batcho

def nth_prime_number(n):
    prime_list = [2]
    num = 3
    while len(prime_list) < n:
        for p in prime_list: # TODO: we only need to check up to the square root of the number
            if num % p == 0:
                break
        else:
            prime_list.append(num)
        num += 2
    return prime_list[n-1]

class ComputeNthPrime(mlpr.Processor):
    NAME='ComputeNthPrime'
    VERSION='0.1.1'
    
    n=mlpr.IntegerParameter('The integer n.')
    output=mlpr.Output('The output text file.')

    def __init__(self):
        mlpr.Processor.__init__(self)

    def run(self):
        prime=nth_prime_number(self.n)
        with open(self.output,'w') as f:
            f.write('{}'.format(prime))

def main():
    parser = argparse.ArgumentParser(
        description='Listen for batches as a compute resource')
    parser.add_argument('command', help='start or stop')
    parser.add_argument('--force_run', help='force run of processors',action="store_true")
    parser.add_argument('--use_container', help='try running jobs in a singularity container',action='store_true')

    args = parser.parse_args()

    batch_name='primes_batch_1'
    container=''
    if args.use_container:
        #container='../../mountaintools/containers/mountaintools_basic/mountaintools_basic.simg'
        container='sha1://228fdbb3e64b1fc463d50c1be9e4ec2d4951aa4a/mountaintools_basic.simg'
    compute_resource='test_resource_01'

    if args.command=='stop':
        batcho.stop_batch(batch_name=batch_name)
    elif args.command=='start':
        list=np.arange(10011,10031)
        jobs=[
            ComputeNthPrime.createJob(
                n=int(n),
                output={'ext':'.txt'},
                _force_run=args.force_run,
                _container=container
            )
            for n in list
        ]

        mlpr.executeBatch(jobs=jobs,num_workers=None,compute_resource=compute_resource,batch_name=batch_name)

        for i,n in enumerate(list):
            result0=jobs[i]['result']
            val=int(ca.loadText(path=result0['outputs']['output']))
            print('The {}th prime number is {}'.format(n,val))
    else:
        raise Exception('Invalid command: {}'.format(command))


if __name__== "__main__":
    main()
