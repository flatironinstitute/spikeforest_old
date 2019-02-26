#!/bin/bash

# trap 'kill $(jobs -p)' EXIT

bin/kbucket-hub test_nodes/test_kbhub1 --auto &
bin/kbucket-host test_nodes/test_kbshare1 --auto
