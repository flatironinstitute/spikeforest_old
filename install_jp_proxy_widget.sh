#!/bin/bash

# jpwidget
pip install jupyterlab
pip install jp_proxy_widget
jupyter nbextension enable --py --sys-prefix jp_proxy_widget
jupyter labextension install jp_proxy_widget
jupyter labextension install @jupyter-widgets/jupyterlab-manager