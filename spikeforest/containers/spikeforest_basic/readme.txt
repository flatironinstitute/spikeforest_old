# first build (if needed)
docker build -t magland/spikeforest_basic .

# then push to docker hub (if needed)
docker push magland/spikeforest_basic

# then create singularity image
./build_simg.sh
