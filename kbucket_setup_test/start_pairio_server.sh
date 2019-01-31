#!/bin/bash

export PAIRIO_ADMIN_TOKEN="secret-pairio-admin-token"

cd ../repos/pairio
npm install
PORT=11001 npm run server