FROM ubuntu:18.04

RUN apt-get update && apt-get install -y unzip
RUN apt-get install -y libxt-dev
RUN apt-get install -y curl 

RUN mkdir /working
RUN curl http://ssd.mathworks.com/supportfiles/downloads/R2019b/Release/1/deployment_files/installer/complete/glnxa64/MATLAB_Runtime_R2019b_Update_1_glnxa64.zip > /working/MATLAB_Runtime_R2019b_Update_1_glnxa64.zip

WORKDIR /working
RUN unzip MATLAB_Runtime_R2019b_Update_1_glnxa64.zip
RUN ./install -mode silent -agreeToLicense yes

# Important not to set the LD_LIBRARY_PATH for Matlab until later, because it conflicts with curl!
##################################################################################################################
RUN apt-get update && apt-get install -y --no-install-recommends gnupg2 curl ca-certificates && \
    curl -fsSL https://developer.download.nvidia.com/compute/cuda/repos/ubuntu1804/x86_64/7fa2af80.pub | apt-key add - && \
    echo "deb https://developer.download.nvidia.com/compute/cuda/repos/ubuntu1804/x86_64 /" > /etc/apt/sources.list.d/cuda.list && \
    echo "deb https://developer.download.nvidia.com/compute/machine-learning/repos/ubuntu1804/x86_64 /" > /etc/apt/sources.list.d/nvidia-ml.list && \
    apt-get purge --autoremove -y curl && \
    rm -rf /var/lib/apt/lists/*

ENV CUDA_VERSION 10.0.130

ENV CUDA_PKG_VERSION 10-0=$CUDA_VERSION-1

# For libraries in the cuda-compat-* package: https://docs.nvidia.com/cuda/eula/index.html#attachment-a
RUN apt-get update && apt-get install -y --no-install-recommends \
        cuda-cudart-$CUDA_PKG_VERSION \
        cuda-compat-10-0 && \
    ln -s cuda-10.0 /usr/local/cuda && \
    rm -rf /var/lib/apt/lists/*

# Required for nvidia-docker v1
RUN echo "/usr/local/nvidia/lib" >> /etc/ld.so.conf.d/nvidia.conf && \
    echo "/usr/local/nvidia/lib64" >> /etc/ld.so.conf.d/nvidia.conf

ENV PATH /usr/local/nvidia/bin:/usr/local/cuda/bin:${PATH}
ENV LD_LIBRARY_PATH /usr/local/nvidia/lib:/usr/local/nvidia/lib64

# nvidia-container-runtime
ENV NVIDIA_VISIBLE_DEVICES all
ENV NVIDIA_DRIVER_CAPABILITIES compute,utility
ENV NVIDIA_REQUIRE_CUDA "cuda>=10.0 brand=tesla,driver>=384,driver<385 brand=tesla,driver>=410,driver<411"
##################################################################################################################

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
### Install spikodrome_utils from github
RUN mkdir -p /src && git clone https://github.com/spikodrome/spikodrome_utils /src/spikodrome_utils \
    && cd /src/spikodrome_utils \
    && git checkout 3c1aec30494f2b4a96939a99270436562c02c494 \
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