exports.KBucketClient=KBucketClient;

const PairioClient=require('pairio').PairioClient;
const axios = require('axios');

function KBucketClient() {
    let that=this;
	let m_share_ids=[]; // default share ids
	let m_url='https://kbucket.flatironinstitute.org';
	let m_verbose=true;
	let m_pairio_client=new PairioClient();

	// config: share_ids, url, verbose
	this.setConfig=function(config) {
		if ('share_ids' in config) {
			m_share_ids=JSON.parse(JSON.stringify(config.share_ids));
		}
		if ('url' in config) {
			m_url=config.url;
		}
		if ('verbose' in config) {
			m_verbose=config.verbose;
		}
	}

	this.setPairioConfig=function(config) {
		m_pairio_client.setConfig(config);
	}

	// opts: share_ids, collection, key
	this.findFile=async function(path,opts) {
        opts=opts||{};
		if (opts.key) {
			if (opts.path) {
				throw Error('If opts.key is given, path must be null.');
			}
			let sha1=await m_pairio_client.get(opts.key);
			if (!sha1) {
				return null;
			}
			return await that.findFile('sha1://'+sha1);
		}
		let obj=await find_file_helper(path,opts);
		if (!obj) {
			return null;
		}
		return obj['path'];
	}
    
    // opts: key
    this.loadObject=async function(path,opts) {
        let url=await that.findFile(path,opts);
        if (!url) return null;
        let obj=await http_get_json(url);
        return obj;
    }

	// opts: share_ids, collection
	async function find_file_helper(path,opts) {
		opts=opts||{};
		let share_ids;
		if (opts.share_ids) {
			share_ids=opts.share_ids;
		}
		else {
			share_ids=m_share_ids;
		}

		let collections;
		if (opts.collection) {
			collections=[opts.collection];
		}
		else {
			collections=null;
		}

		let sha1;
		if (path.startsWith('sha1://')) {
			let list=path.split('/');
			sha1=list[2]||null;
			if (!sha1) {
				throw Error('Invalid sha1 path: '+path);
			}
		}
		else if (path.startsWith('kbucket://')) {
			let list=path.split('/');
			let share_id0=list[2];
			if (!share_id0) {
				throw Error('Invalid kbucket path: '+path);
			}
			share_id0=await filter_share_id(share_id0);
			share_ids=[share_id0];
			let path0=list.slice(3).join('/');
			let prv=await get_prv_for_kbucket_file(share_ids[0],path0);
			sha1=prv['original_checksum'];
		}
		else {
			throw Error('Unsupported path: '+path);
		}

		for (let ii in share_ids) {
			let share_id0=share_ids[ii];
			let aa=await find_in_share(share_id0,sha1);
			if (aa) {
				return {
					path:aa.url,
					size:aa.size,
					sha1:sha1
				};
			}
		}
		return null;
	}

	let filter_share_id_cache={};
	async function filter_share_id(id) {
		if (id in filter_share_id_cache) {
			return filter_share_id_cache[id];
		}
		let list=id.split('.');
		if (list.length==2) {
			let ret=await m_pairio_client.get(list[1],{collection:list[0]});
			if (ret) {
				filter_share_id_cache[id]=ret;
			}
			return ret;
		}
		else {
			return id;
		}
	}

	async function get_prv_for_kbucket_file(share_id,path) {
		let url=m_url+'/'+share_id+'/prv/'+path;
		let obj=await http_get_json(url);
		return obj;
	}

	async function find_in_share(share_id,sha1) {
		share_id=await filter_share_id(share_id);
		let url=m_url+'/'+share_id+'/api/find/'+sha1;
		let obj=await http_get_json(url);
		if (!obj['success']) {
			throw Error('Error finding file in share: '+obj['error']);
		}
		if (!obj['found']) {
			return null;
		}
    let urls0=obj['urls'];
    results0=obj['results'];
    for (let i in urls0) {
    	let url0=urls0[i];
    	let accessible=await test_url_accessible(url0);
    	if (accessible) {
	    	return {
	    		url:url0,
	    		size:results0[0]['size']
	    	};
	    }
    }
    return null;
	}
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
	});
}

async function test_url_accessible(url) {
	return new Promise(function(resolve,reject) {
		axios.head(url, {
      responseType: 'json'
    })
    .then(function(response) {
    	resolve(response.status==200);
    })
    .catch(function(error) {
    	resolve(false);
    });
	});
}