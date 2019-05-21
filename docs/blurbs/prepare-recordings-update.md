## Prepare recordings update

21 May 2019

A few updates withe method for preparing recordings, mainly for J Jun.

The ground truth base directory in the `prepare_*_recordings.py` files has been switched from

`kbucket://15734439d8cf/groundtruth`

to 

`/mnt/home/jjun/ceph/groundtruth`

This is more straightforward, and requires that the prepare scripts are run on
the cluster at Flatiron. Once the prepare scripts have run, then we can access
the files from anywhere, if we have the proper spikeforest.kbucket download token.
Further, unlike before, it automatically creates the snapshot and uploads the files
to kachery, so that no longer needs to be a separate step.

Another change is that, with the exception of boyden32c, the first recording in each
study is also uploaded to spikeforest.public, and is therefore publicly accessible.

