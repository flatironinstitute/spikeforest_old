FROM node
MAINTAINER Jeremy Magland
EXPOSE 24341
VOLUME /cairioserver

ADD . /src
RUN cd /src && \
  npm install .
WORKDIR /cairioserver
ENTRYPOINT [ "/src/docker_entry.sh" ]
