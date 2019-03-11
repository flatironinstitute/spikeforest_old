FROM ubuntu:18.04

RUN echo "12 February 2019"

#########################################
### Python, etc                                                                                                                
RUN apt-get update && apt-get -y install git wget build-essential
RUN apt-get install -y python3 python3-pip
RUN ln -s python3 /usr/bin/python
RUN ln -s pip3 /usr/bin/pip
RUN DEBIAN_FRONTEND=noninteractive apt-get install -y python3-tk

#########################################
RUN mkdir /src
RUN git clone https://github.com/flatironinstitute/spikeforest /src/spikeforest && cd /src/spikeforest
WORKDIR /src/spikeforest
RUN pip install -e ./mountaintools
RUN pip install -e ./spikeforest
