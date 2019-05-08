FROM ubuntu:18.04

#########################################
### Python, etc                                                                                                                
RUN apt-get update && apt-get -y install git wget build-essential
RUN apt-get install -y python3 python3-pip
RUN ln -s python3 /usr/bin/python
RUN ln -s pip3 /usr/bin/pip
RUN DEBIAN_FRONTEND=noninteractive apt-get install -y python3-tk

RUN echo "8 May 2019"

RUN mkdir -p /src

#########################################
### Herding spikes 2
RUN pip install joblib
RUN pip install numpy
RUN git clone https://github.com/mhhennig/hs2 /src/hs2 && cd /src/hs2 && git checkout bb810abdab33f1319a1a51224705bd33a173868d
WORKDIR /src/hs2
RUN python setup.py develop
RUN mkdir -p herdingspikes/probes && mkdir -p herdingspikes/probe_info

### spikeextractors
RUN pip install spikeextractors==0.4.2

### Other dependencies
RUN pip install requests
