import os, sys
import unittest
def append_to_path(dir0): # A convenience function
    if dir0 not in sys.path:
        sys.path.append(dir0)
append_to_path(os.getcwd()+'/..')
from kbucket import client as kb
 
class Test001(unittest.TestCase):
    def setUp(self):
        pass
        
    def tearDown(self):
        pass
     
    def test_001(self):
        a=kb.readDir('.')
        print(a)


 
if __name__ == '__main__':
    unittest.main()
