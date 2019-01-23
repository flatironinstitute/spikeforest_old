FROM ubuntu:18.04

#########################################
### Python, etc                                                                                                                
RUN apt-get update && apt-get -y install git wget build-essential
RUN apt-get install -y python3 python3-pip
RUN ln -s python3 /usr/bin/python
RUN ln -s pip3 /usr/bin/pip
RUN DEBIAN_FRONTEND=noninteractive apt-get install -y python3-tk

RUN echo "23 January 2019"

#########################################
### spikeforest2
RUN mkdir /src
RUN git clone https://github.com/flatironinstitute/spikeforest2 /src/spikeforest2
WORKDIR /src/spikeforest2
RUN pip install -r requirements.txt
RUN python setup.py develop

#########################################
### Spyking Circus
RUN apt-get update && apt-get install -y libopenmpi-dev
RUN pip install spyking-circus
RUN pip install pyqt5
RUN apt-get update && apt-get install -y libglib2.0-0
RUN apt-get update && apt-get install -y libgl1-mesa-glx
RUN apt-get update && apt-get install -y qt5-default
RUN apt-get update && apt-get install -y packagekit-gtk3-module
RUN apt-get update && apt-get install -y libcanberra-gtk-module libcanberra-gtk3-module
#RUN DEBIAN_FRONTEND=noninteractive apt-get install -y xserver-xorg xorg jwm

