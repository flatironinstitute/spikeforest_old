FROM ubuntu:18.04

#########################################
### Python, etc                                                                                                                
RUN apt-get update && apt-get -y install git wget build-essential
RUN apt-get install -y python3 python3-pip
RUN ln -s python3 /usr/bin/python
RUN ln -s pip3 /usr/bin/pip
RUN DEBIAN_FRONTEND=noninteractive apt-get install -y python3-tk

RUN echo "26 June 2019"

#########################################
### Klusta
RUN pip install Cython h5py tqdm
RUN pip install scipy
RUN pip install click klusta klustakwik2

### spikeextractors
RUN pip install spikeextractors==0.4.2
RUN pip install spiketoolkit==0.3.4
RUN pip install spikesorters==0.1.0

### Other dependencies
RUN pip install requests

ENV LANG C.UTF-8  
ENV LC_ALL C.UTF-8 