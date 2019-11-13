FROM ubuntu:18.04

RUN echo "7 February 2019"

#########################################
### Python, etc                                                                                                                
RUN apt-get update && apt-get -y install git wget build-essential
RUN apt-get install -y python3 python3-pip
RUN ln -s python3 /usr/bin/python
RUN ln -s pip3 /usr/bin/pip
RUN DEBIAN_FRONTEND=noninteractive apt-get install -y python3-tk

#########################################
### spikeforest2
RUN mkdir /src
RUN git clone https://github.com/flatironinstitute/spikeforest2 /src/spikeforest2
WORKDIR /src/spikeforest2
RUN pip install -r requirements.txt
RUN python setup.py develop

#########################################
### Install yass, a previous version
RUN mkdir /src
RUN git clone https://github.com/paninski-lab/yass.git /src/yass
WORKDIR /src/yass
RUN git checkout tags/0.5
RUN python2 setup.py develop

## call yass via python2 /path/to/binary/yass
