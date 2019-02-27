# first build (if needed)
docker build -t jamesjun/yass .

# then push to docker hub (if needed)
docker push jamesjun/yass

# then create singularity image
./build_simg.sh
