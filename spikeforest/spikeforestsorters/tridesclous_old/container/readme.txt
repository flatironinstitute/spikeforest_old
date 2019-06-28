# first build (if needed)
docker build -t magland/tridesclous .

# then push to docker hub (if needed)
docker push magland/tridesclous

# then create singularity image
./build_simg.sh
