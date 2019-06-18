FROM ubuntu:18.04

RUN echo "17 June 2019"

#########################################
### Python, etc                                                                                                                
RUN apt-get update && apt-get -y install git wget build-essential
RUN apt-get install -y python3 python3-pip
RUN ln -s python3 /usr/bin/python
RUN ln -s pip3 /usr/bin/pip
RUN DEBIAN_FRONTEND=noninteractive apt-get install -y python3-tk

#########################################
### Tridesclous
RUN apt-get update && apt-get install -y libgl1-mesa-glx
RUN pip install scipy numpy pandas scikit-learn matplotlib seaborn tqdm openpyxl PyQt5 pyqtgraph==0.10 quantities neo
RUN pip install tridesclous>=1.2.1

## OpenCL with POCL
RUN apt-get update && apt-get install -y opencl-headers ocl-icd-opencl-dev libclc-dev ocl-icd-libopencl1 pocl-opencl-icd
RUN pip install pyopencl

### spikeextractors
RUN pip install spikeextractors==0.4.2

### spiketoolkit
RUN pip install spiketoolkit==0.3.3

### Other dependencies
RUN pip install requests h5py
