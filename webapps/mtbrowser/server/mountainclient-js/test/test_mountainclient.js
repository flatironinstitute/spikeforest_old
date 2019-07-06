#!/usr/bin/env node

const MountainClient = require('..').MountainClient;

let mt = new MountainClient();

async function main() {
    let val = await mt.getValue({collection: 'spikeforest', key:'kbucket'});

    mt.configDownloadFrom('spikeforest.public');

    let txt = await mt.loadText('key://pairio/spikeforest/testing.index.js');
    if (!txt) {
        console.error('Problem loading text');
    }
    else {
        console.info(`Loaded text of length ${txt.length}`);
    }

    let key0 = {
        "name": "unit-details-v0.1.0",
        "recording_directory": "sha1dir://b84ca6cdc7536ea0eb2fea753d5cb3786ffda3cc.paired_boyden32c/624_5_2",
        "firings_true": "sha1dir://b84ca6cdc7536ea0eb2fea753d5cb3786ffda3cc.paired_boyden32c/624_5_2/firings_true.mda",
        "firings": "sha1://187a99c69dafb3d5bdc6f3279d63627d5115fdb5/firings_out.mda"
    };

    let val0 = await mt.getValue({collection: 'spikeforest', key:key0});
    console.log('val0:', val0);

    let val1 = await mt.loadObject(null, {collection: 'spikeforest', key:key0});
    console.log('val1:', val1);

}

main();

