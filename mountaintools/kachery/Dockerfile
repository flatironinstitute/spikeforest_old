FROM node
EXPOSE 25481
VOLUME /share

ADD . /kachery
RUN cd /kachery && npm install .
WORKDIR /share
