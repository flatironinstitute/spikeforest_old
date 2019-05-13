# first build (if needed)
docker build -t magland/klusta .

# then push to docker hub (if needed)
docker push magland/klusta

# then create singularity image
./build_simg.sh
