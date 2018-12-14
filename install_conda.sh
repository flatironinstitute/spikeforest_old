#!/bin/bash

conda install python=3.6
pip install -r requirements.txt

# jpwidget
pip install jupyterlab
pip install jp_proxy_widget
jupyter nbextension enable --py --sys-prefix jp_proxy_widget
jupyter labextension install jp_proxy_widget
jupyter labextension install @jupyter-widgets/jupyterlab-manager

# colab
pip install jupyter_http_over_ws
jupyter serverextension enable --py jupyter_http_over_ws

python setup.py develop