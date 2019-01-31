#!/bin/bash

export PAIRIO_ADMIN_TOKEN="secret-pairio-admin-token"
export PAIRIO_URL="http://localhost:11001"
export PAIRIO_USER="magland"
export PAIRIO_USER_TOKEN="6220c9dae511"

cd ../repos/pairio
pairioserver/pairio register $PAIRIO_USER $PAIRIO_USER_TOKEN