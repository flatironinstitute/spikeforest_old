import numpy as np
import os, sys
import unittest
def append_to_path(dir0): # A convenience function
    if dir0 not in sys.path:
        sys.path.append(dir0)
append_to_path(os.getcwd()+'/..')
from pairio import client as pa
 
class Test001(unittest.TestCase):
    def setUp(self):
      pass
        
    def tearDown(self):
        pass
     
    def test_001(self):
      key0='testkey'
      val0='testval000'
      pa.set(key0,val0)
      val=pa.get(key0)
      self.assertEqual(val,val0)
      pa.set(key0,val0+'abc')
      val=pa.get(key0)
      self.assertEqual(val,val0+'abc')


 
if __name__ == '__main__':
    unittest.main()
