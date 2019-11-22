FROM nvidia/cuda:10.1-base-ubuntu18.04

RUN apt-get update && apt-get install -y unzip
RUN apt-get install -y libxt-dev
RUN apt-get install -y curl 

RUN mkdir /install_matlab \
    && curl http://ssd.mathworks.com/supportfiles/downloads/R2019b/Release/1/deployment_files/installer/complete/glnxa64/MATLAB_Runtime_R2019b_Update_1_glnxa64.zip > /install_matlab/MATLAB_Runtime_R2019b_Update_1_glnxa64.zip \
    && cd /install_matlab && unzip MATLAB_Runtime_R2019b_Update_1_glnxa64.zip && ./install -mode silent -agreeToLicense yes && cd / && rm -rf /install_matlab

# See comment above
ENV LD_LIBRARY_PATH /usr/local/MATLAB/MATLAB_Runtime/v97/runtime/glnxa64:/usr/local/MATLAB/MATLAB_Runtime/v97/bin/glnxa64:/usr/local/MATLAB/MATLAB_Runtime/v97/sys/os/glnxa64:/usr/local/MATLAB/MATLAB_Runtime/v97/extern/bin/glnxa64

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

#########################################
### Compiled irc
COPY run_irc /run_irc

# python packages
RUN pip install spikeextractors==0.7.0 spiketoolkit==0.5.0 spikesorters==0.2.1
RUN pip install kachery==0.4.2

#########################################
### Install spikeforest_container_utils from github
RUN mkdir -p /src && git clone https://github.com/flatironinstitute/spikeforest /src/spikeforest \
    && cd /src/spikeforest \
    && git checkout d9d5d82dd031fa9e3546ad090ed9ec0e811ddf95 \
    && cd future_containers/spikeforest_container_utils \
    && pip install -e .
RUN pip install h5py

RUN mkdir -p /src && git clone https://github.com/flatironinstitute/ironclust /src/ironclust
ENV IRONCLUST_PATH=/src/ironclust
ENV PATH="~/MATLAB/R2019b/bin:${PATH}"

RUN chmod a+x /run_irc

COPY ironclust.py /src/ironclust.py
COPY ironclust_sorter.py /src/ironclust_sorter.py
COPY shellscript.py /src/shellscript.py

ENTRYPOINT ["python", "/src/ironclust.py", "--output", "/output"]