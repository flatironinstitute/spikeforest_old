FROM ubuntu:18.04

#########################################
### Python, etc                                                                                                                
RUN apt-get update && apt-get -y install git wget build-essential
RUN apt-get install -y python3 python3-pip
RUN ln -s python3 /usr/bin/python
RUN ln -s pip3 /usr/bin/pip
RUN DEBIAN_FRONTEND=noninteractive apt-get install -y python3-tk

RUN echo "29 March 2019 b"

RUN mkdir /src

#########################################
### MountainSort
RUN pip install pybind11
RUN pip install isosplit5
RUN git clone https://github.com/magland/ml_ms4alg /src/ml_ms4alg
WORKDIR /src/ml_ms4alg
RUN python setup.py develop

##################################################################
# spikeforest (but not mountaintools -- because that gets injected at runtime)
RUN git clone https://github.com/flatironinstitute/spikeforest /src/spikeforest && cd /src/spikeforest
WORKDIR /src/spikeforest
RUN pip install -e ./spikeforest