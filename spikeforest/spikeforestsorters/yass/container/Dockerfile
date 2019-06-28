FROM ubuntu:18.04

#########################################
### Python, etc                                                                                                                
RUN apt-get update && apt-get -y install git wget build-essential
RUN apt-get install -y python3 python3-pip
RUN ln -s python3 /usr/bin/python
RUN ln -s pip3 /usr/bin/pip
RUN DEBIAN_FRONTEND=noninteractive apt-get install -y python3-tk

RUN echo "6 May 2019"

#########################################
### Install yass, a previous version
RUN pip install tensorflow==1.13.0rc1
RUN git clone https://github.com/paninski-lab/yass.git /src/yass && cd /src/yass && git checkout tags/0.5
WORKDIR /src/yass
RUN pip install -r requirements.txt
RUN python setup.py install

### spikeextractors
RUN pip install spikeextractors==0.4.2

### Other dependencies
RUN pip install requests