FROM ubuntu:18.04

RUN echo "21 February 2019"

#########################################
### Python, etc                                                                                                                
RUN apt-get update && apt-get -y install git wget build-essential
RUN apt-get install -y python3 python3-pip
RUN ln -s python3 /usr/bin/python
RUN ln -s pip3 /usr/bin/pip
RUN DEBIAN_FRONTEND=noninteractive apt-get install -y python3-tk

#########################################
### mountaintools
RUN mkdir /src
RUN git clone https://github.com/flatironinstitute/spikeforest /src/spikeforest && cd /src/spikeforest
WORKDIR /src/spikeforest
RUN pip install -e ./mountaintools

#########################################
# python2 and pip2 (but keep python 3 as the default)
RUN apt-get install -y python-pip
RUN apt-get install -y libyaml-dev #libpython2.7-dev
#RUN rm /usr/bin/python && ln -s python3 /usr/bin/python
#RUN rm /usr/bin/pip && ln -s pip3 /usr/bin/pip

#########################################
### Install yass, a previous version
#RUN mkdir /src
RUN git clone https://github.com/paninski-lab/yass.git /src/yass && cd /src/yass && git checkout tags/0.5
WORKDIR /src/yass
RUN pip install -r requirements.txt
RUN python setup.py install

## call yass via python2 /path/to/binary/yass

### spikeforest
WORKDIR /src/spikeforest
RUN pip3 install -e ./spikeforest
