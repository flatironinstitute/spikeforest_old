FROM ubuntu:18.04

#########################################
### Python, etc                                                                                                                
RUN apt-get update && apt-get -y install git wget build-essential
RUN apt-get install -y python3 python3-pip
RUN ln -s python3 /usr/bin/python
RUN ln -s pip3 /usr/bin/pip
RUN DEBIAN_FRONTEND=noninteractive apt-get install -y python3-tk

RUN echo "29 March 2019"

#########################################
# spikeforest dependencies
RUN pip install numpy scipy matplotlib requests pillow pandas ipython h5py setuptools-git scikit-learn python-frontmatter
RUN pip install spikeextractors==0.4.2
