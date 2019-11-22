FROM ubuntu:18.04

#########################################
### Python                                                               
RUN apt-get update && apt-get -y install git wget build-essential
RUN apt-get install -y python3 python3-pip
RUN ln -s python3 /usr/bin/python
RUN ln -s pip3 /usr/bin/pip
RUN DEBIAN_FRONTEND=noninteractive apt-get install -y python3-tk

#########################################
### Numpy
RUN pip install numpy

#########################################
### Make sure we have python3 and a working locale
RUN rm /usr/bin/python && ln -s python3 /usr/bin/python && rm /usr/bin/pip && ln -s pip3 /usr/bin/pip
ENV LANG='en_US.UTF-8' LANGUAGE='en_US:en' LC_ALL='en_US.UTF-8'
RUN apt-get install -y locales && locale-gen en_US.UTF-8

# python packages
RUN pip install spikeextractors==0.7.0 spiketoolkit==0.5.0 spikesorters==0.2.1
RUN pip install ml_ms4alg==0.3.2
RUN pip install kachery==0.4.2

#########################################
### Install spikodrome_utils from github
RUN mkdir -p /src && git clone https://github.com/spikodrome/spikodrome_utils /src/spikodrome_utils \
    && cd /src/spikodrome_utils \
    && git checkout 3c1aec30494f2b4a96939a99270436562c02c494 \
    && pip install -e .

COPY mountainsort4.py /src/mountainsort4.py

ENTRYPOINT ["python", "/src/mountainsort4.py", "--output", "/output"]