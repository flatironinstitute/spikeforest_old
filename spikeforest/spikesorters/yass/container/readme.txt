# first build (if needed)
docker build -t magland/yass .

# then push to docker hub (if needed)
docker push magland/yass

# then create singularity image
./build_simg.sh
