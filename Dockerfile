FROM gitpod/workspace-full:latest

ADD requirements.txt /work/requirements.txt

RUN pip install -r /work/requirements.txt
