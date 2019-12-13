FROM ubuntu:18.04

#########################################
### Python, etc
RUN apt-get update && apt-get -y install git wget build-essential
RUN apt-get install -y python3 python3-pip
RUN ln -s python3 /usr/bin/python
RUN ln -s pip3 /usr/bin/pip
RUN DEBIAN_FRONTEND=noninteractive apt-get install -y python3-tk

RUN echo "13 November 2019"

#########################################
### Spyking Circus
RUN apt-get update && apt-get install -y libmpich-dev mpich
RUN pip install spyking-circus==0.8.8
RUN pip install pyqt5
RUN apt-get update && apt-get install -y libglib2.0-0
RUN apt-get update && apt-get install -y libgl1-mesa-glx
RUN apt-get update && apt-get install -y qt5-default
RUN apt-get update && apt-get install -y packagekit-gtk3-module
RUN apt-get update && apt-get install -y libcanberra-gtk-module libcanberra-gtk3-module
#RUN DEBIAN_FRONTEND=noninteractive apt-get install -y xserver-xorg xorg jwm

### spikeinterface
RUN pip install spikeextractors==0.5.5
RUN pip install spiketoolkit==0.4.0
RUN mkdir /src && git clone https://github.com/spikeinterface/spikesorters /src/spikesorters && cd /src/spikesorters && git checkout e5b275dba262719cf6947e9092b3363fc63dcbcb && pip install .

### Other dependencies
RUN pip install requests

ENV LANG C.UTF-8  
ENV LC_ALL C.UTF-8 
