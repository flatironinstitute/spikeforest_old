#!/usr/bin/env python

import os
import sys
import argparse
import sfdata as sf
import batcho
import time
import mlprocessors as mlpr  # needed to register the mlprocessors batcho commands
import traceback

# This can be important for some of the jobs in certain situations
os.environ['DISPLAY'] = ''


def main():
    parser = argparse.ArgumentParser(
        description='Listen for batches as a compute resource')
    parser.add_argument('batch_name', help='Name of the batch to run')

    args = parser.parse_args()

    try:
        batcho.run_batch(batch_name=args.batch_name)
    except Exception as err:
        traceback.print_exc()
        print('Error running batch:', err)
        sys.exit(-1)


if __name__ == "__main__":
    main()
