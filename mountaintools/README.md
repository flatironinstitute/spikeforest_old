# MountainTools

A collection of tools for creating shareable and reproducible scientific workflows. It is used by [SpikeForest](https://github.com/flatironinstitute/spikeforest).

MountainTools provides

* A formal method for defining well-defined Python procedures that operate on input parameters and files and produce output files. These are known as *Processors*.
* Automatic execution of *Processors* inside [singularity](https://sylabs.io/docs/) containers
* Automatic caching of results from *Processor* runs
* Job management, batching, and queing mechanisms for *Processor* runs
* Parallelization capabilities and automated running of processing batches on compute clusters
* Functions for storing files, text, and objects (JSON-serializable Python dicts) in local and remote databases
* Content-addressible storage databases (kacheries)
* A key/value storage database (pairio)
* Tools for working with `sha1://` and `sha1dir://` URIs

The Python package is installable via

```
pip install mountaintools
```

and comprises the following modules:

* [**mlprocessors**](mlprocessors/README.md) - utilities for MountainTools *Processors*, jobs, batches, parallelization, and running batches on a compute cluster
* [**mountainclient**](mountainclient/README.md) - for working with `sha1://` and `sha1dir://` URIs, accessing the local MountainTools databases, and interacting with remote kacheries (content-addressible storage databases).
* [**vdomr**](vdomr) - for building GUIs using a mix of Python and JavaScript that may be run in notebooks, in the browser, or on the desktop. This will eventually be separated out and maintained as its own Python package.

This repository also contains JavaScript / NodeJS code for running pairio and kachery servers.

## Installation
To install mountaintools the easiest approach is to use pip. Open your terminal emulator and type in the following command:
```
pip install mountaintools
```

**Note:** Depending on your environment you might need to substitute `pip` with `pip3` as mountaintools works only with Python 3.

For information on using mountaintools see [mountainclient](mountainclient), [mlprocessors](mlprocessors), and [vdomr](vdomr).


### Setting kachery tokens
For interacting with kachery servers it is required that mountaintools knows about access tokens to upload or download files.
For that you need to put the tokens into `~/.mountaintools/kachery_tokens` file.

This file is a text file with three column records in each row.
Each record consists of a server name or URL, token type (currently `upload` or `download`) and finally token contents.

You can modify this file by hand but it is suggested that you rather use `kachery-token` which comes with mountaintools.
To add a token run a command similar to `kachery-token add companylab.spike download ***tokendata***` replacing `***tokendata***` with the actual token.

You can list registered tokens with `kachery-token list`. 

```
companylab.spike    download    l***5
http://127.0.0.1    upload      p***w
```

The tool will mask away token data. To unmask it run the tool with `--show-tokens` option.

```
companylab.spike    download    l51umhmqjp35
http://127.0.0.1    upload      pnu8oyw6oyjw
```

## Tools

Mountaintools comes with a set of commands that can be invoked from a terminal.
Their aim is to provide a quick way to perform common tasks of manipulating objects stored in remote mountain databases.

### mt-cat
Writes contents of a local or remote file to stdout.

```bash
mt-cat [-h] [--download-from DOWNLOAD_FROM] path
```

This is a very simplified equivalent of `cat` where you can pass in a compatible mountaintools URI path and it will try to locate the given file and retrieve it if available and then print its contents to standard output.

You can optionally pass in `--download-from` option together with a name of a server where you expect to find the file.

### mt-download
Retrieves a file and places it in a given destination path.
```bash
mt-download [-h] [--verbose] [--download-from DOWNLOAD_FROM] src_path dst_path
```

This tool can be treated as an equivalent of `cp` command. `src_path` should be a mountaintools URI pointing to a file or directory and `dst_path` should be a path in your filesystem where to place retrieved data.

You can optionally pass in `--download-from` option together with a name of a server where you expect to find the file.

### mt-find
This tool finds the given file and prints its location.

```bash
mt-find [-h] [--verbose] [--local-only] [--remote-only] [--download-from DOWNLOAD_FROM] path
```

By default it searches both local and remote locations but it can be restricted using `--local-only`
or `--remote-only` switches.

If the file is found, its local path is printed to standard output. If the entity represents a directory
then that information is printed instead of the path.

### mt-ls
This tool lists the contents of a local or remote directory expressed as a `sha1dir://` address.

```bash
usage: mt-ls [-h] [--download-from DOWNLOAD_FROM] path

List the contents of a remote database directory

positional arguments:
  path                  Local or remote path (sha1dir://...)

optional arguments:
  -h, --help            show this help message and exit
  --download-from DOWNLOAD_FROM
```


### mt-resolve-key-path
This tool resolves a key:// entry into a real (local or remote) path.

```bash
usage: mt-resolve-key-path [-h] key_path

Display the resolved path associated with a key://... path.

positional arguments:
  key_path    Path to local file or directory

optional arguments:
  -h, --help  show this help message and exit
```

### mt-snapshot

Compute the hash of a local or remote file or directory and print the address representing a snapshot.
```
usage: mt-snapshot [-h] [--upload-to UPLOAD_TO] [--download-recursive]
                   [--upload-recursive] [--login]
                   path [dest_path]

Compute the hash of a local or remote file or directory and print the 
address representing a snapshot.

positional arguments:
  path                  Path to local file or directory
  dest_path             Optional destination key path

optional arguments:
  -h, --help            show this help message and exit
  --upload-to UPLOAD_TO, -u UPLOAD_TO
                        Remote database to upload all files
  --download-recursive, --dr
                        Download all remote files to the local SHA-1 cache.
  --upload-recursive, --ur
                        Upload all files (recursively).
  --login               Whether to log in
```

After the snapshot is computed, the file can optionally be uploaded to one or more servers (defined with `--upload-to`).

