FROM ubuntu:18.04

#########################################
### Python, etc                                                                                                                
RUN apt-get update && apt-get -y install git wget build-essential
RUN apt-get install -y python3 python3-pip
RUN ln -s python3 /usr/bin/python
RUN ln -s pip3 /usr/bin/pip
RUN DEBIAN_FRONTEND=noninteractive apt-get install -y python3-tk

RUN echo "6 May 2019"

RUN mkdir /src

#########################################
### MountainSort
RUN pip install pybind11
RUN pip install isosplit5
RUN git clone https://github.com/magland/ml_ms4alg /src/ml_ms4alg
WORKDIR /src/ml_ms4alg
RUN python setup.py develop

### spikeextractors
RUN pip install spikeextractors==0.4.2

### Other dependencies
RUN pip install requests