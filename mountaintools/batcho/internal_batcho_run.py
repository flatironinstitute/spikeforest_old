#!/usr/bin/env python

import os
import sys
import argparse
import spikeforest as sf
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
    parser.add_argument(
        '--randomize_order', help='Run jobs in randomized order (helpful for parallel processing)', action='store_true')

    args = parser.parse_args()

    try:
        batcho.run_batch(batch_name=args.batch_name,
                         randomize_order=args.randomize_order)
    except Exception as err:
        traceback.print_exc()
        print('Error running batch:', err)
        sys.exit(-1)


if __name__ == "__main__":
    main()
