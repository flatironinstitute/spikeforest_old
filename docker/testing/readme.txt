# First build the test docker container:
docker build -t test_spikeforest2 .

# Next run the test command (note that you need to fill in the password)
docker run -it test_spikeforest2 bash -c "SPIKEFOREST_PASSWORD=xxxxxxxx bin/sf_run_batch --clear --test_one --mlpr_force_run summarize_recordings_magland_synth"

