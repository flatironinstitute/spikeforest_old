# first build (if needed)
docker build -t magland/spyking_circus .

# then push to docker hub (if needed)
docker push magland/spyking_circus

# then create singularity image
./build_simg.sh
