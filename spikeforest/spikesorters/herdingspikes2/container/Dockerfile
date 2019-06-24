FROM ubuntu:18.04

#########################################
### Python, etc                                                                                                                
RUN apt-get update && apt-get -y install git wget build-essential
RUN apt-get install -y python3 python3-pip
RUN ln -s python3 /usr/bin/python
RUN ln -s pip3 /usr/bin/pip
RUN DEBIAN_FRONTEND=noninteractive apt-get install -y python3-tk

RUN echo "21 June 2019"

### spikeextractors
RUN pip install spikeextractors==0.5.2

### spiketoolkit
RUN pip install spiketoolkit==0.3.4

#########################################
### Herding spikes 2
RUN pip install joblib
RUN pip install numpy
RUN pip install herdingspikes==0.3.2

### Other dependencies
RUN pip install requests
