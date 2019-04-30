#!/bin/bash

set -e

../../../spike-front/admin/bin/delete-data.js mongodb://localhost:27017/spikefront --delete
../../../spike-front/admin/bin/format-and-load-data.js $1 mongodb://localhost:27017/spikefront
