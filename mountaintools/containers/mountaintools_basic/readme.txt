# first build (if needed)
docker build -t magland/mountaintools_basic .

# then push to docker hub (if needed)
docker push magland/mountaintools_basic

# then create singularity image
./build_simg.sh
