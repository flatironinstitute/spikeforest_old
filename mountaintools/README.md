# mountaintools

This is home for `mountaintools`, a Python package for accessing ...

- [mlprocessors](mlprocessors)      - create mountain processors in Python   
- [kachery](kachery)
- [kbucketserver](kbucketserver)
- [mountainclient](mountainclient)  - access to local and remote mountain databases and KBucket shares
- [pairio](pairio)
- [pairioserver](pairioserver)
- [mtlogging](mtlogging)
- [vdomr](vdomr)

## Installation
To install mountaintools the easiest approach is to use pip. Open your terminal emulator and type in the following command:
```
pip install mountaintools
```

For information on using mountaintools see [mountainclient](mountainclient).


### Setting kachery tokens
For interacting with kachery servers it is required that mountaintools knows about access tokens to upload or download files.
For that you need to put the tokens into `~/.mountaintools/kachery_tokens` file.

This file is a text file with three column records in each row.
Each record consists of a server name or URL, token type (currently `upload` or `download`) and finally token contents.

You can modify this file by hand but it is suggested that you rather use `kachery-token` which comes with mountaintools.
To add a token run a command similar to `kachery-token add spikeforest.public download ***tokendata***` replacing `***tokendata***` with the actual token.

You can list registered tokens with `kachery-token list`. 

```
spikeforest.public  download    3***9
http://127.0.0.1    upload      f***8
```

The tool will mask away token data. To unmask it run the tool with `--show-tokens` option.

```
spikeforest.public  download    3662816cdc1ac55c1dc36a8f5b48573b464f9659
http://127.0.0.1    upload      fdcd406bd0937b23e650f9666930ea123fc1f748
```
