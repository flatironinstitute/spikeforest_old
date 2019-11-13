## Making a SpikeForest recording public

For testing purposes, we would like to make a subset of our recordings
publicly available. Here we show the procedure for accomplishing this.

The first step is to get a `sha1dir://` URI associated with the recording. This is done
by taking a mt-snapshot using mountaintools. For example,

```
cd /path/to/synth_maglandc
mt-snapshot datasets_noise10_K10_C4
```

This will print something like `sha1dir://cdc2bd6b5a39223b53b8bd2fcbe8594fc780325e`.

After configuring the appropriate upload kachery upload token, we can then make
a single recording publicly available via:

```
mt-snapshot sha1dir://cdc2bd6b5a39223b53b8bd2fcbe8594fc780325e/001_synth --ur --dr --upload-to spikeforest.public
mt-snapshot sha1://cdc2bd6b5a39223b53b8bd2fcbe8594fc780325e --upload-to spikeforest.public
```

This will upload the contents of this recording directory to a kachery node that
is configured to be publicly accessible for downloads. The `--ur` and `--dr`
flags are documented via the `--help` switch. The second line is needed to also
upload the index of the higher-level directory. (In the future we should do this
automatically - @wysota)

Now, anyone can download this dataset via

```
mt-download sha1dir://cdc2bd6b5a39223b53b8bd2fcbe8594fc780325e/001_synth 001_synth --download-from spikeforest.public
```

If it is already cached on their machine it will not need to download (saving us
bandwidth).

Alternatively, from Python:

```python
from mountaintools import client as mt

mt.configDownloadFrom('spikeforest.public')

local_path = mt.realizeFile(path='sha1dir://cdc2bd6b5a39223b53b8bd2fcbe8594fc780325e/001_synth/raw.mda')
```

Or via SpikeExtractors

```python
from spikeforest import SFMdaRecordingExtractor, SFMdaSortingExtractor

mt.configDownloadFrom('spikeforest.public')

# Load an example tetrode recording with its ground truth
recdir = 'sha1dir://cdc2bd6b5a39223b53b8bd2fcbe8594fc780325e/001_synth'

print('loading recording...')
recording = SFMdaRecordingExtractor(dataset_directory=recdir, download=True)
sorting_true = SFMdaSortingExtractor(firings_file=recdir + '/firings_true.mda')
```

The spike sorting tutorial linked from the Algorithms page of the website makes
use of this mechanism.



