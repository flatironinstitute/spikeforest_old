#!/usr/bin/env python

# Right now the central pairio server is hosted on https://pairio.org:20443

# This is a linode server

# Inside a tmux session called cairio:

# cd ~/src/spikeforest2/mountaintools/cairioserver
# See .env file containing:

# PORT=20443
# CAIRIO_ADMIN_TOKEN=******
# To run the server:

# npm install .
# node cairioserver.js
# There are instructions in the home directory for setting up firewall and renewing the certs

import os
from mountaintools import client as mt
from dotenv import load_dotenv

# Load secret stuff from the spikeforest.env file (only on the admin's computer)
print('Loading secret stuff from spikeforest.env')
load_dotenv(dotenv_path='spikeforest.env', verbose=True)
CAIRIO_ADMIN_TOKEN = os.environ['CAIRIO_ADMIN_TOKEN']
mt.setPairioToken('admin', CAIRIO_ADMIN_TOKEN)

# Let's set the tokens for the remote collections
print('Setting tokens for the remote pairio collections')
mt.addRemoteCollection(collection='spikeforest', token=os.environ['PAIRIO_SPIKEFOREST_TOKEN'], admin_token=CAIRIO_ADMIN_TOKEN)
mt.addRemoteCollection(collection='morley', token=os.environ['PAIRIO_MORLEY_TOKEN'], admin_token=CAIRIO_ADMIN_TOKEN)

# Set up the kachery aliases
print('Setting up the kachery aliases')
mt.setValue(key='kbucket', value='http://kbucket.flatironinstitute.org', collection='spikeforest')
mt.setValue(key='public', value='http://45.79.176.243:8080', collection='spikeforest')
mt.setValue(key='public1', value='http://132.249.245.245:24341', collection='spikeforest')
mt.setValue(key='public2', value='http://132.249.245.245:24342', collection='spikeforest')
mt.setValue(key='public3', value='http://132.249.245.245:24343', collection='spikeforest')
