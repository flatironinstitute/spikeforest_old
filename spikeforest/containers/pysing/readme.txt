# build the docker container and push to docker hub
docker build -t magland/pysing .
docker push magland/pysing

# Enter shell within the container
docker run -it magland/pysing bash

# you may want to mount the kbucket cache directory
-v $KBUCKET_CACHE_DIR:/tmp/sha1-cache
