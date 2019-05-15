FROM node
MAINTAINER Jeremy Magland
EXPOSE 24341
VOLUME /pairioserver

ADD . /src
RUN cd /src && \
  npm install .
WORKDIR /pairioserver
ENTRYPOINT [ "/src/docker_entry.sh" ]
