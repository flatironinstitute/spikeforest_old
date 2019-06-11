#!/bin/bash

set -e

../../../spike-front/admin/bin/delete-news-posts.js mongodb://localhost:27017/spikefront --delete
../../../spike-front/admin/bin/load-news-posts.js $1 mongodb://localhost:27017/spikefront
