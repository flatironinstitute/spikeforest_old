FROM ubuntu:18.04

#########################################
### Python, etc                                                                                                                
RUN apt-get update && apt-get -y install git wget build-essential
RUN apt-get install -y python3 python3-pip
RUN ln -s python3 /usr/bin/python
RUN ln -s pip3 /usr/bin/pip
RUN DEBIAN_FRONTEND=noninteractive apt-get install -y python3-tk

RUN echo "30 May 2019"

#########################################
# Singularity 2.6.1
# See: https://www.sylabs.io/guides/2.6/user-guide/quick_start.html#quick-installation-steps
RUN git clone https://github.com/sylabs/singularity.git /singularity
WORKDIR /singularity
RUN git fetch --all && git checkout 2.6.1
RUN apt-get update && apt-get install -y libtool m4 automake libarchive-dev
RUN ./autogen.sh
RUN ./configure --prefix=/usr/local
RUN make
RUN make install

#########################################
# For convenience
RUN apt-get update && apt-get install -y nano curl