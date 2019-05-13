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
### Tridesclous
RUN pip install https://github.com/tridesclous/tridesclous/archive/master.zip

### spikeextractors
RUN pip install spikeextractors==0.4.2

### Other dependencies
RUN pip install requests

### This belongs above in the Tridesclous section
RUN apt-get update && apt-get install -y libgl1-mesa-glx

