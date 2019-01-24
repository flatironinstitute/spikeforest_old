FROM gitpod/workspace-full:latest

ADD requirements.txt

RUN pip install -r requirements.txt
