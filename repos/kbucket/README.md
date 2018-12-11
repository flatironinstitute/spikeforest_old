# KBucket

System for sharing data for scientific research.

Developers: Jeremy Magland, with contributions from Dylan Simon and Alex Morley

Flatiron Institute, a divison of Simons Foundation

## Philosophy

In many scientific fields it is essential to be able to exchange, share, archive, and publish experimental data. However, raw data files needed to reproduce results can be enormous. The philosophy of KBucket is to separate file contents from the files themselves, and to host data content where it most naturally lives, that is, in the lab where it was generated. By replacing large data files by tiny universal pointers called .prv files (analogous to magnet links in torrent), we open diverse ways for sharing datasets, studies, and results.

For example, sometimes it is useful to email data to a collaborator, while other times it's convenient to post it to slack, or to maintain a study on github, or share a directory structure on dropbox, or google drive, or post it to a website or forum. However, if the file sizes are many Gigabytes or even Terabytes, many of those options become unfeasible without a system like KBucket.

## Installation

**Supported operating systems**: Linux and OS X

The easiest way to install kbucket is via conda:

```
conda install -c flatiron kbucket
```

Alternatively, you can install from source after obtaining a [recent version of NodeJS](https://github.com/flatironinstitute/mountainlab-js/blob/master/docs/docs_editable/prerequisites.md).

Clone this repository and install using npm:

```
cd kbucket
npm install
```

Then add `kbucket/bin` to your `PATH` environment variable.

## Overview and usage

### Sharing a directory of data with the system

```
cd /path/to/data/directory
kbucket-host .
```

You will then be prompted to interactively configure the share, as follows:

```
magland@dub:~/kbucket_data/datasets/dataset_01$ kbucket-host .
Creating new kbucket share configuration in /home/magland/kbucket_data/datasets/dataset_01/.kbucket ...
Initializing configuration...

? Name for this KBucket share: dataset_01
? Are sharing this data for scientific research purposes (yes/no)? yes
? Brief description of this KBucket share: Example kbucket data directory.
? Owner's name (i.e., your full name): Jeremy Magland
? Owner's email (i.e., your email): my@email.edu
? Share all data recursively contained in the directory /home/magland/kbucket_data/datasets/dataset_01? (yes/no) yes
? Listen url for this hub (use . for http://localhost:[port]): .
? Connect to hub: https://kbucket.flatironinstitute.org

kbucket-share is running http on port 2000
Connecting to parent hub: https://kbucket.flatironinstitute.org
Starting indexing...
Connected to parent hub: kbucket.flatironinstitute.org
Web interface: https://kbucketgui.herokuapp.com/?share=cf59975225e0
Indexed 7 files.
```

Note that the files of the share are now browseable/downloadable via a web interface as indicated in the output from kbucket.

Let's go through what all this means, and what has actually happened.

I am now hosting a new kbucket share (kb-share), which allows other researchers to access the files within this shared directory provided that they know the ID of the share (in this case `cf59975225e0`) or the SHA-1 hashes of those files (or the corresponding .prv files). Here are some details on the configuration options:

**Name for the kb-share.** This is simply a name that could be useful for logging or other miscellaneous purposes.

**Sharing for scientific research purposes?** This system is intended only for scientific research purposes, and therefore users are required to type "yes". We don't want people using KBucket to share illegal media content, for example. It's not easy to enforce this, but at least we make it clear that this would be a no-no.

**Brief description.** It is useful to report a description of the kb-share.

**Owner's name and email.** If a particular kb-share is acting suspiciously, it's helpful to be able to contact that user by e-mail, as a warning, before blacklisting particular shares.

**Confirm share recursive?** The user is required to type "yes" so they understand that they are exposing data in that directory to the general internet.

**Connect to hub.** This crucial field specifies the url of the kbucket hub we are connecting to. More about hubs below.

KBucket will create a new directory called .kbucket within this shared directory where it will store the configuration as well as a private/public RSA PEM key pair. The configuration options entered are contained in the .kbucket/kbnode.json file and can be edited by hand if needed.

To stop sharing the directory, simply use [ctrl]+c to cancel the process. To begin sharing again, use the above command. The configuration will be remembered as the default, but you will be prompted to verify the answers again, unless you use the --auto flag as follows:

```
cd /path/to/data/directory
kbucket-host . --auto
```

This is useful if you don't want to press [enter] a bunch of times.

### Providing access to shared files

Once kbucket-host is running, and assuming we are connected to a hub within the KBucket network, the files in this directory can be accessed from any computer on the internet via http/https. However, one piece of information is needed in order to locate and download any particular file: the SHA-1 hash of the file. Much like a magnet link for torrent, this serves as the universal locator for that file. This file hash is contained (along with some other information) in the .prv file.

You can download .prv files corresponding to files in your share via the web interface mentioned above, or to create a .prv file on your local computer, simply execute

```
kb-prv-create /path/to/data/directory/file1.dat file1.dat.prv
```

This will create a new, tiny text file called file1.dat.prv containing the SHA-1 hash required to locate the file on the system KBucket. Now send that file (email/slack/google-drive/github/dropbox) to your collaborator in order to provide access. Your colleague can then download (retrieve) the file via:

```
kb-prv-download file1.dat.prv file1.dat
```

Or, to locate the file without downloading:

```
kb-prv-find file1.dat.prv file1.dat
```

If the file is very large, it may be more convenient to load only portions of the file (the http/https protocol for KBucket supports the range header). Therefore our file1.dat.prv could be passed as an input to a visualizer that incrementally loads only parts of the file needed for viewing. There are many other advantages of the .prv file system for enabling web applications and data analysis on remote machines. These will be discussed elsewhere.

It is also possible to create a .prvdir file encapsulating the .prv information for all the files in a particular directory.

```
kb-prv-create /path/to/data/directory directory.prvdir
```

This creates a relatively small JSON text file that can be also be shared with colleagues, and integrated into user interfaces or processing pipelines.

### What's actually happening with the data?

Note that the .prv file contains no information about the computer it was created on. No ip addresses, routing information, etc. It simply contains the SHA-1 hash, the size of the file, and a couple other fields for convenience. Since we assume that the SHA-1 hash is sufficient to uniquely identify the file, that is the only piece of information needed to locate and retrieve the file content. This is useful because sometimes we need to change the names of files and directories, or move data from one computer to another, or replicate data on several servers. 

### Shares and hubs: the KBucket network

The KBucket network is organized as a collection of disjoint trees. The root node of the main tree is hosted by us (https://kbucket.flatironinstitute.org), but you can easily create your own network (disconnected from ours) with your own root node. For simplicity let's just consider it as one big connected tree for now.

The leaves of the tree are called kb-shares and the other nodes are called kb-hubs. As mentioned there is one root kb-hub hosted by us. Each other kb-node (kb-share or kb-hub) is connected to a single parent kb-hub via websocket. Each kb-share sends (via websocket) the SHA-1 hashes of all the files in its directory to its parent hub who maintains an index for fast lookup. Because all of the kb-nodes are connected to one another by a network of sockets, any of the kb-hubs may be queried with the hash to retrieve the corresponding original file's location.

Once the client (computer trying to retrieve the file) knows the URL to the kb-share containing the desired file, it can access that file content directly via http request without burdening the other computers in the network. This is particularly important since we wouldn't want all network traffic passing through the root node.

But what if the kb-share hosting the file is behind a firewall? This is where the network of kb-hubs becomes important. If the client cannot access the share computer directly, it will try its parent hub, and then that hub's parent, etc. In the worst case it will need to access the file from the root node (which of course has an open public port). In any case, the file content will be proxied through the websockets and piped to the client.

There is opportunity for quite a bit of optimization in this framework in terms of intelligent caching, and determining the optimal way to deliver content from one location to another. Since at this point, there is very little demand on the system, such optimizations are lower priority for the time being.

### Hosting your own hub

When creating a new kb-share, one of the configuration options is to specify the URL for the parent kb-hub. By default this is the root node hosted by us. But there are several reasons why this is not ideal. First, if you are behind a firewall, then all content transferred outside of your internal network will need to pass through our hub (might become slow). Second, you may not trust the stability of our server. Third, you may share data with colleagues on a nearby or faster network. In general it does not make sense for the most kb-shares to be directly connected to the same root node. Therefore, you will probably want to direct your share to one of our sub-hubs (to be specified later), or to simply host your own.

The first step is to determine a server that you will use to host the hub. Ideally this should be a computer with a port open to the wider internet, but this is not a strict requirement. For example, if you primarily need to share files within your own organization, then a hub within the firewall could be useful. Also, if you want to use your hub to access data from web applications, you should also get a SSL certificate for your server/hub so that you can serve content via https (web pages that are served over https can only access content from servers that are also running https [question: is this really true?]).

Configuring a kb-hub is very much like configuring a kb-share. First create a directory to be associated with your hub and then run

```
cd /path/to/hubdir
kbucket-hub .
```

Again, the system will guide you through an interactive configuration, for example:

```
magland@dub:~/kbucket_hubs/hub1$ kbucket-hub .
Initializing configuration...

? Name for this KBucket hub: hub1
? Are you hosting this hub for scientific research purposes (yes/no)? yes
? Brief description of this KBucket hub: hub1
? Owner's name (i.e., your full name): Jeremy Magland
? Owner's email (i.e., your email): my@email.edue
? Listen port for this hub: 3240
? Listen url for this hub (use . for http://localhost:[port]): .
? Parent hub url (use . for none): https://kbucket.flatironinstitute.org

kbucket-hub is running http on port 3240
Connecting to parent hub: https://kbucket.flatironinstitute.org
Connected to parent hub: kbucket.flatironinstitute.org
Web interface: https://kbucketgui.herokuapp.com/?hub=dbb538702881

```

Many of the configuration fields are the same as for a share, but there are a couple of new options:

**Listen port.** This is the port to listen on. For simplicity, if this port number ends with the digits 443 (e.g., 10443) then it will use the https protocol (finding the certificates in the kbucket/src/encryption directory). Otherwise it will listen using http.

**Listen URL.** By default this will be `http://localhost:[listen_port]`, but if you want this hub to be accessible to the wider network, you should put in a domain name. While you could use an ip address, it is better to obtain a domain name for a hub that is made available via https to the wider internet.

As mentioned above, each kb-hub can be connected to a parent hub. If you choose not to connect to a parent, then your local KBucket network will still function, but your colleages at remote locations may not be able to access your content. Therefore, it's usually a good idea to point your hub to a hub that is already part of the network.

That's it! Now your hub is listening for incoming websocket connections from kb-shares or other kb-hubs. So configure your shares to point to your hub's listen URL and start sharing files.
