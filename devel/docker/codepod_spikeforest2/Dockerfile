FROM magland/codepod:latest

# python packages
RUN . /venv/bin/activate && pip install jupyterlab numpy matplotlib requests pillow pandas h5py scipy ipython ipywidgets six
RUN . /venv/bin/activate && pip install pytest pytest-cov idna autopep8


# jp_proxy_widget for vdomr in jupyterlab
# RUN . /venv/bin/activate && pip install jp_proxy_widget
# RUN . /venv/bin/activate && jupyter nbextension enable --py --sys-prefix jp_proxy_widget
# RUN . /venv/bin/activate && jupyter labextension install jp_proxy_widget
# RUN . /venv/bin/activate && jupyter labextension install @jupyter-widgets/jupyterlab-manager
