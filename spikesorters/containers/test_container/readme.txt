# first build (if needed)
docker build -t magland/test_container .

# then push to docker hub (if needed)
docker push magland/test_container

# then create singularity image
./build_simg.sh
