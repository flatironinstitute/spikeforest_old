FROM magland/theiapod

RUN . /venv/bin/activate && pip install jupyterlab
RUN . /venv/bin/activate && pip install numpy matplotlib requests fasteners pillow pandas h5py scipy ipython jsonschema numexpr ipywidgets numpydoc

RUN npm install -g nodemon

# jp_proxy_widget for vdomr in jupyterlab
RUN . /venv/bin/activate pip install jp_proxy_widget
RUN . /venv/bin/activate jupyter nbextension enable --py --sys-prefix jp_proxy_widget
RUN . /venv/bin/activate jupyter labextension install jp_proxy_widget
RUN . /venv/bin/activate jupyter labextension install @jupyter-widgets/jupyterlab-manager
