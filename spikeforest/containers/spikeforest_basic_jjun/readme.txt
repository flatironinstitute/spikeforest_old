# first build (if needed)
docker build -t jamesjun/spikeforest_basic .

# then push to docker hub (if needed)
docker push jamesjun/spikeforest_basic

# then create singularity image
./build_simg.sh
