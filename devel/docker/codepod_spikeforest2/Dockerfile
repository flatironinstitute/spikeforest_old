FROM magland/codepod:latest

RUN . /venv/bin/activate && pip install jupyterlab numpy matplotlib requests pillow pandas h5py scipy ipython ipywidgets

# Node and Yarn
RUN curl -sL https://deb.nodesource.com/setup_8.x | bash -
RUN apt-get update && apt-get install -y nodejs
RUN npm install -g yarn

# nodemon
RUN npm install -g nodemon

# jp_proxy_widget for vdomr in jupyterlab
# RUN . /venv/bin/activate && pip install jp_proxy_widget
# RUN . /venv/bin/activate && jupyter nbextension enable --py --sys-prefix jp_proxy_widget
# RUN . /venv/bin/activate && jupyter labextension install jp_proxy_widget
# RUN . /venv/bin/activate && jupyter labextension install @jupyter-widgets/jupyterlab-manager
