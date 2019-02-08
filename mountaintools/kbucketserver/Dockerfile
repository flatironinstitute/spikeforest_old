FROM node
MAINTAINER Jeremy Magland
EXPOSE 24341
VOLUME /share

ADD . /src
RUN cd /src && \
  mv /src/docker/scripts_inside_docker /scripts && \
  npm install .
WORKDIR /share
