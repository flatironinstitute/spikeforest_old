FROM gitpod/workspace-full

RUN pip install jupyterlab
RUN pip install numpy matplotlib requests fasteners pillow pandas h5py scipy ipython jsonschema numexpr ipywidgets numpydoc

RUN npm install -g nodemon

# jp_proxy_widget for vdomr in jupyterlab
RUN pip install jp_proxy_widget
RUN jupyter nbextension enable --py --sys-prefix jp_proxy_widget
RUN jupyter labextension install jp_proxy_widget
RUN jupyter labextension install @jupyter-widgets/jupyterlab-manager
