#!/bin/bash

set -e

../../../spike-front/admin/bin/delete-data.js mongodb://localhost:27017/spikefront --delete
../../../spike-front/admin/bin/format-and-load-data.js $PWD/website_data mongodb://localhost:27017/spikefront