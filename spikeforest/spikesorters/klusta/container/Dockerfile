FROM ubuntu:18.04

#########################################
### Python, etc                                                                                                                
RUN apt-get update && apt-get -y install git wget build-essential
RUN apt-get install -y python3 python3-pip
RUN ln -s python3 /usr/bin/python
RUN ln -s pip3 /usr/bin/pip
RUN DEBIAN_FRONTEND=noninteractive apt-get install -y python3-tk

RUN echo "13 May 2019"

#########################################
### Klusta
RUN pip install Cython h5py tqdm
RUN pip install click klusta klustakwik2

### spikeextractors
RUN pip install spikeextractors==0.4.2

### Other dependencies
RUN pip install requests

# the following belongs above in the "Klusta" section
RUN pip install scipy

ENV LANG C.UTF-8  
ENV LC_ALL C.UTF-8 