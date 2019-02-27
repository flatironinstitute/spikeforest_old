FROM spikeforest/codepod:latest

# jp_proxy_widget for vdomr in jupyterlab
RUN . /venv/bin/activate \
    && pip install jupyterlab jp_proxy_widget \
    && jupyter nbextension enable --py --sys-prefix jp_proxy_widget \
    && jupyter labextension install jp_proxy_widget \
    && jupyter labextension install @jupyter-widgets/jupyterlab-manager

# python packages
RUN . /venv/bin/activate \
    && pip install jupyterlab numpy matplotlib \
       requests pillow pandas h5py scipy \
       ipython ipywidgets six

RUN apt-get update && apt-get install -y tmux vim

RUN . /venv/bin/activate \
    && pip install pytest pytest-cov idna autopep8
