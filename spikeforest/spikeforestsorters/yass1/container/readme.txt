# first build (if needed)
docker build -t jamesjun/yass1 .

# then push to docker hub (if needed)
docker push jamesjun/yass1

# then create singularity image
./build_simg.sh
