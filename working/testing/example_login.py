#!/usr/bin/env python

from mountaintools import client as mt

def main():
    # You can set the MOUNTAIN_USER and MOUNTAIN_PASSWORD in ~/.mountaintools/.env
    # Then the following will automatically log you in
    # The interactive=True means that if those variables are not set, the system will prompt the user
    mt.login(interactive=True)

    # You can also explicitly provide the user and/or passord
    # The following will prompt for the password for testuser
    mt.login(user='testuser', interactive=True)

    # Configure mountaintools to use a particular remote collection and kbucket share
    # If the logged-in user has proper permissions, then the appropriate access tokens
    # are automaticall provided.
    mt.configRemoteReadWrite(collection='spikeforest',share_id='69432e9201d0')

    # Test the remote connection
    # (Note that if we were not connected to a remote collection/share,
    # then the following would still work -- just stored in a local disk-database)
    mt.setValue(key=dict(test='key'), value='testval')
    print(mt.getValue(key=dict(test='key')))

main()