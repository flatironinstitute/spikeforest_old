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
RUN git clone https://github.com/jamesjun/HS2 /src/hs2 && cd /src/hs2 && git checkout 
#RUN git clone https://github.com/mhhennig/hs2 /src/hs2 && cd /src/hs2 && git checkout 286e9db6e6896e1526139fe156c66eeebeea546a
WORKDIR /src/hs2
RUN python setup.py develop

### spikeextractors
RUN pip install spikeextractors==0.4.2

### Other dependencies
RUN pip install requests
