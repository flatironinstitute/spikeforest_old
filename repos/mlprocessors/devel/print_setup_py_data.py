from contextlib import contextmanager
import sys, os

@contextmanager
def suppress_stdout():
    with open(os.devnull, "w") as devnull:
        old_stdout = sys.stdout
        sys.stdout = devnull
        try:  
            yield
        finally:
            sys.stdout = old_stdout

import setuptools
import json

global_data={
  "output":''
}
def setup(**kwargs):
  global_data['output']=json.dumps(kwargs,indent=2)
setuptools.setup = setup
content = open('setup.py').read()
with suppress_stdout():
  exec(content)

print(global_data['output'])
