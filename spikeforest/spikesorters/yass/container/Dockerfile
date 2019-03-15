FROM ubuntu:18.04

#########################################
### Python, etc                                                                                                                
RUN apt-get update && apt-get -y install git wget build-essential
RUN apt-get install -y python3 python3-pip
RUN ln -s python3 /usr/bin/python
RUN ln -s pip3 /usr/bin/pip
RUN DEBIAN_FRONTEND=noninteractive apt-get install -y python3-tk

RUN echo "15 March 2019"

#########################################
### mountaintools
RUN mkdir /src
RUN git clone https://github.com/flatironinstitute/spikeforest /src/spikeforest && cd /src/spikeforest
WORKDIR /src/spikeforest
RUN pip install -e ./mountaintools

#########################################
### Install yass, a previous version
#RUN mkdir /src
RUN git clone https://github.com/paninski-lab/yass.git /src/yass && cd /src/yass && git checkout tags/0.5
WORKDIR /src/yass
RUN pip install -r requirements.txt
RUN python setup.py install

RUN pip install tensorflow==1.13.0rc1

### spikeforest
WORKDIR /src/spikeforest
RUN pip3 install -e ./spikeforest
