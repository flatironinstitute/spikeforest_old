FROM ubuntu:18.04

#########################################
### Python, etc                                                                                                                
RUN apt-get update && apt-get -y install git wget build-essential
RUN apt-get install -y python3 python3-pip
RUN ln -s python3 /usr/bin/python
RUN ln -s pip3 /usr/bin/pip

RUN echo "force run 4"
RUN git clone https://github.com/flatironinstitute/spikeforest2 /working/spikeforest2
WORKDIR /working/spikeforest2
RUN pip install -r requirements.txt
RUN python setup.py develop

# Try this after setting SPIKEFOREST_PASSWORD environment variable
# bin/sf_run_batch --clear --test_one --mlpr_force_run summarize_recordings_magland_synth