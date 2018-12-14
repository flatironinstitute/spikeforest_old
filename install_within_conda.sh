#!/bin/bash

pip install -r requirements.txt

# colab
pip install jupyter_http_over_ws
jupyter serverextension enable --py jupyter_http_over_ws

python setup.py develop