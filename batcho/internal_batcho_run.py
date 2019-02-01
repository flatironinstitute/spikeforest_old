#!/usr/bin/env python

import os
import sys
import argparse
import spikeforest as sf
import batcho
import time
from kbucket import client as kb
import mlprocessors as mlpr ## needed to register the mlprocessors batcho commands

# This can be important for some of the jobs in certain situations
os.environ['DISPLAY']=''

def main():
  parser = argparse.ArgumentParser(description = 'Listen for batches as a compute resource')
  parser.add_argument('batch_name',help='Name of the batch to run')

  args = parser.parse_args()

  BATCHO_CONFIG_NAME=os.environ.get('BATCHO_CONFIG_NAME',None)
  BATCHO_CONFIG_COLLECTION=os.environ.get('BATCHO_CONFIG_COLLECTION',None)
  BATCHO_CONFIG_PASSWORD=os.environ.get('BATCHO_CONFIG_PASSWORD',None)

  if BATCHO_CONFIG_NAME and BATCHO_CONFIG_COLLECTION and BATCHO_CONFIG_PASSWORD:
      pass
  else:
      print('You must set the environment variables: BATCHO_CONFIG_NAME, BATCHO_CONFIG_COLLECTION, BATCHO_CONFIG_PASSWORD')
      sys.exit(-1)

  sf.kbucketConfigRemote(name=BATCHO_CONFIG_NAME,collection=BATCHO_CONFIG_COLLECTION,password=BATCHO_CONFIG_PASSWORD)

  batcho.run_batch(batch_name=args.batch_name)

if __name__== "__main__":
  main()
  
