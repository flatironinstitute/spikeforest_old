FROM ubuntu:18.04

#########################################
### Python, etc                                                                                                                
RUN apt-get update && apt-get -y install git wget build-essential
RUN apt-get install -y python3 python3-pip
RUN ln -s python3 /usr/bin/python
RUN ln -s pip3 /usr/bin/pip

RUN echo "8 February 2019"

#########################################
### mountaintools
RUN mkdir /src
RUN git clone https://github.com/flatironinstitute/spikeforest2 /src/spikeforest2 && cd src/spikeforest2 && git checkout dev2
WORKDIR /src/spikeforest2/mountaintools
RUN pip install -r requirements.txt
RUN python setup.py develop
