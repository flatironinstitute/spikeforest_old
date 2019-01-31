FROM magland/theiapod

RUN . /venv/bin/activate && pip install jupyterlab
RUN . /venv/bin/activate && pip install numpy matplotlib requests fasteners pillow pandas h5py scipy ipython jsonschema numexpr ipywidgets numpydoc

RUN npm install -g nodemon
