FROM magland/theiapod

RUN . /venv/bin/activate && pip install jupyterlab
RUN . /venv/bin/activate && pip install numpy matplotlib requests fasteners pillow pandas h5py scipy ipython jsonschema numexpr ipywidgets numpydoc

RUN npm install -g nodemon

# jp_proxy_widget for vdomr in jupyterlab
RUN . /venv/bin/activate && pip install jp_proxy_widget
RUN . /venv/bin/activate && jupyter nbextension enable --py --sys-prefix jp_proxy_widget
RUN . /venv/bin/activate && jupyter labextension install jp_proxy_widget
RUN . /venv/bin/activate && jupyter labextension install @jupyter-widgets/jupyterlab-manager

# Singularity
RUN apt-get install -y libarchive-dev
RUN VERSION=2.5.2 && wget https://github.com/singularityware/singularity/releases/download/$VERSION/singularity-$VERSION.tar.gz && tar xvf singularity-$VERSION.tar.gz && cd singularity-$VERSION && ./configure --prefix=/usr/local && make && make install