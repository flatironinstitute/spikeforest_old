# first build (if needed)
docker build -t magland/mountainsort4 .

# then push to docker hub (if needed)
docker push magland/mountainsort4

# then create singularity image
./build_simg.sh
