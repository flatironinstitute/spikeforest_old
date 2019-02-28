import numpy as np
import os, sys
import unittest


def append_to_path(dir0):  # A convenience function
    if dir0 not in sys.path:
        sys.path.append(dir0)


append_to_path(os.getcwd() + '/..')
from spikeforest import spikewidgets as sw


class Test001(unittest.TestCase):
    def setUp(self):
        pass

    def tearDown(self):
        pass

    def test_toy_example1(self):
        IX, OX = sw.example_datasets.toy_example1()


if __name__ == '__main__':
    unittest.main()
