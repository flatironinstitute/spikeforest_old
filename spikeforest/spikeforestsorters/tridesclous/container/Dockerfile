FROM ubuntu:18.04

# FROM nvidia/opencl  ### SOON


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
RUN pip install Cython
RUN pip install scipy numpy pandas scikit-learn matplotlib seaborn tqdm openpyxl PyQt5 pyqtgraph==0.10 quantities neo numba hdbscan
RUN pip install tridesclous==1.3.1

### spikeinterface
RUN pip install --upgrade https://github.com/SpikeInterface/spikeextractors/archive/master.zip
RUN pip install --upgrade https://github.com/SpikeInterface/spiketoolkit/archive/master.zip
RUN pip install --upgrade https://github.com/SpikeInterface/spikesorters/archive/master.zip

## OpenCL/NVIDIA
# tridesclous will be slow because without opencl
# RUN apt-get update && apt-get install -y opencl-headers ocl-icd-opencl-dev libclc-dev ocl-icd-libopencl1 clinfo
# RUN pip install pyopencl

# ### Other dependencies
# RUN pip install requests h5py
