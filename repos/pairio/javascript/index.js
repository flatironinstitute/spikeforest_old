exports.PairioClient=PairioClient;
exports.test_pairioclient=test_pairioclient;

const stringify = require('json-stable-stringify');
const crypto = require('crypto');
const axios = require('axios');

function PairioClient() {
	let m_collections=[]; // default collections
	let m_url='https://pairio.org:10443';
	let m_verbose=false;

	this.setConfig=function(config) {
		if ('collections' in config) {
			m_collections=JSON.parse(JSON.stringify(config.collections));
		}
		if ('url' in config) {
			m_url=config.url;
		}
		if ('verbose' in config) {
			m_verbose=config.verbose;
		}
	}

	// opts: collection, collections, return_collection
	this.get=async function(key,opts) {
		opts=opts||{};
		let collections=[];
		if ('collection' in opts) {
			collections=[opts.collection];
		}
		else if ('collections' in opts) {
			collections=opts.collections;
		}
		else {
			collections=m_collections;
		}
		let key0=filter_key(key);
		for (let i in collections) {
			let C=collections[i];
			let path=`/get/${C}/${key0}`;
			let url0=m_url+path;
			if (m_verbose) {
				console.info('GET: '+url0);
			}
			let obj;
			try {
				obj=await http_get_json(url0);
			}
			catch(err) {
				console.error('Error in get: '+err.message);
			}
			if (!obj) {
				return null;
			}
			if (obj['success']) {
				if (opts.return_collection) {
					return {value:obj['value'],collection:C};
				}
				else {
					return obj['value'];
				}
			}
		}
		return null;
	}
}

function filter_key(key) {
	if (typeof(key)=='string') {
		return key;
	}
	else if (typeof(key)=='object') {
		return sha1_of_object(key);
	}
	else {
		throw Error('Unexpected type of key in filter_key: '+typeof(key));
	}
}

function sha1_of_object(obj) {
  let shasum = crypto.createHash('sha1');
  shasum.update(stringify(obj));
  return shasum.digest('hex');
}

async function http_get_json(url) {
	return new Promise(function(resolve,reject) {
		axios.get(url, {
      responseType: 'json'
    })
    .then(function(response) {
    	resolve(response.data);
    })
    .catch(function(error) {
    	reject(error);
    });
	})
}

async function test_pairioclient() {
	let client=new PairioClient();
	client.setConfig({collections:['magland']});
	let key0='test';
	let val0=await client.get(key0);
	console.info(`Value for key=${key0}: ${val0}`);
}
