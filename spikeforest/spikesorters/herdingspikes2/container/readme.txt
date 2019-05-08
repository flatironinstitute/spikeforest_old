# first build (if needed)
docker build -t magland/herdingspikes2 .

# then push to docker hub (if needed)
docker push magland/herdingspikes2

# then create singularity image
./build_simg.sh
