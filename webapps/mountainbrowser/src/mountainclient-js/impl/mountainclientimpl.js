exports.MountainClientImpl=MountainClientImpl;

const axios = require('axios');
const crypto = require('crypto');
const stable_stringify = require('json-stable-stringify');
const textEncoding = require('text-encoding');
const TextDecoder = textEncoding.TextDecoder;

function MountainClientImpl(fs) {
  let that = this;
  let m_pairio_url = process.env.PAIRIO_URL||'http://pairio.org';
  let m_sha1_cache_dir = process.env.SHA1_CACHE_DIR || process.env.KBUCKET_CACHE_DIR || '/tmp/sha1-cache';
  let m_download_from = [];
  let m_memory_cache = new MemoryCache();
  let m_local_file_cache = new LocalFileCache(m_sha1_cache_dir, fs);
  let m_kachery_urls = {};

  this.setParioUrl = function(url) {
    m_pairio_url = url;
  }
  this.configDownloadFrom = function(name_or_list) {
    if (typeof(name_or_list) === 'string') {
      if (m_download_from.indexOf(name_or_list) >= 0)
        return;
      m_download_from.push(name_or_list);
    }
    else if (typeof(name_or_list) == 'object') {
      name_or_list.forEach(name => {
        this.configDownloadFrom(name);
      });
    }
  }
  this.getValue = async function(opts) {
    if (((!opts.key) && (!opts.hashed_key)) || (!opts.collection)) {
      console.warn('Missing key/hashed_key or collection in call to getValue().')
      return null;
    }
    let keyhash = opts.hashed_key || hash_of_key(opts.key);
    let path;
    if (!opts.subkey) {
      path = `/get/${opts.collection}/${keyhash}`;
    }
    else {
      path = `/get/${opts.collection}/${keyhash}/${opts.subkey}`;
    }
    let url0 = m_pairio_url + path;
    let obj = await http_get_json(url0);
    if (!obj) return null;
    if (!obj.success) return null;
    return obj.value;
  }
  this.resolveKeyPath = async function(path, opts) {
    let txt = await resolve_key_path(path);
    return txt;
  }
  this.loadObject = async function(path, opts) {
    let txt = await this.loadText(path, opts);
    if (!txt) return null;
    let obj;
    try {
      obj = JSON.parse(txt);
    }
    catch(err) {
      console.warn(`Problem parsing JSON in loadObject for path: ${path}`);
      return null;
    }
    return obj;
  }
  this.loadText = async function(path, opts) {
    let buf = await this.loadBinary(path, opts);
    if (!buf) return null;
    let txt='';
    if ('byteLength' in buf) {
      txt = new TextDecoder("utf-8").decode(new Uint8Array(buf));
      // txt=String.fromCharCode.apply(null, new Uint8Array(buf));
    }
    else {
      txt = buf.toString('utf8');
    }
    return txt;
  }
  this.findFile = async function(path, opts) {
    opts = JSON.parse(JSON.stringify(opts || {}));
    opts.find = true;
    let url_or_null = await this.loadBinary(path, opts);
    return url_or_null;
  }
  this.probeKachery = async function(name, opts) {
    let kachery_url = await resolve_kachery_url(name);
    if (!kachery_url) return false;
    let url0 = kachery_url + '/probe';
    let obj = await http_get_json(url0);
    if (!obj) return false;
    return (obj.success);

  }
  this.fileSha1 = async function(path, opts) {
    if (path.startsWith('sha1://')) {
      let sha1 = path.split('/')[2] || '';
      if (!sha1) return null;
      return sha1;
    }
    else if (path.startsWith('sha1dir://')) {
      let list0 = path.split('/');
      let dir_sha1 = list0[2] || '';
      dir_sha1 = dir_sha1.split('.')[0];
      if (!dir_sha1) return null;
      let dd = await this.loadObject('sha1://'+dir_sha1);
      if (!dd) return null;
      let ii = 3
      while (ii < list0.length) {
          name0 = list0[ii]
          if (name0 in dd['dirs']) {
              dd = dd['dirs'][name0]
          }
          else if (name0 in dd['files']) {
              if (ii + 1 == list0.length) {
                  let sha1 = dd['files'][name0]['sha1'];
                  return sha1;
              }
              else return null;
          }
          else {
              return null;
          }
          ii = ii + 1
      }
      return null;
    }
    else if (path.startsWith('key://')) {
      let newpath = await resolve_key_path(path);
      if (!newpath) return null;
      return this.fileSha1(newpath, opts);
    }
    else {
      return null;
    }
  }
  this.loadBinary = async function(path, opts) {
    opts = opts || {};
    if (!path) {
      if ((opts.collection) && ((opts.key)||(opts.hashed_key))) {
        if (!opts.hashed_key) {
          opts.hashed_key = hash_of_key(opts.key);
        }
        // tilde means it is already hashed
        return await this.loadBinary(`key://pairio/${opts.collection}/~${hash_of_key(opts.key)}`, opts);
      }
      else {
        console.warn('If path is not specified, you must provide collection and key.');
        return null;
      }
    }
    if ((path.startsWith('sha1://')) || (path.startsWith('sha1dir://')) || (path.startsWith('key://'))) {
      let sha1 = await this.fileSha1(path);
      if (!sha1) return null;
      let ret = m_memory_cache.getBinaryForSha1(sha1);
      if (ret !== null) {
        return ret;
      }
      let ret2 = await m_local_file_cache.getBinaryForSha1(sha1);
      if (ret2 !== null) {
        return ret2;
      }
      for (let i=0; i<m_download_from.length; i++) {
        let df = m_download_from[i];
        let kachery_url = await resolve_kachery_url(df);
        if (kachery_url) {
          let url0 = kachery_url + '/get/sha1/' + sha1;
          if (opts.find) {
            let ok = await http_check(url0);
            if (ok) {
              return url0;
            }
            else {
              return null;
            }
          }
          else {
            let buf = await http_get_binary(url0);
            if (buf !== null) {
              m_memory_cache.setBinaryForSha1(sha1, buf);
              await m_local_file_cache.setBinaryForSha1(sha1, buf);
              return buf;
            }
          }
        }
      }
      return null;
    }
    else if ((path.startsWith('http://')) || (path.startsWith('http://'))) {
      if (opts.find) {
        let ok = await http_check(path);
        if (ok) {
          return path;
        }
        else {
          return null;
        }
      }
      else {
        return await http_get_binary(path);
      }
    }
    else {
      console.warn('Unsupported protocol for path: ' + path);
      return null;
    }
  }
  this.readDir = async function(path, opts) {
    // todo
  };

  async function resolve_kachery_url(name) {
    if (name in m_kachery_urls) {
      return m_kachery_urls[name];
    }
    let list0 = name.split('.');
    if (list0.length == 2) {
      let val = await that.getValue({collection: list0[0], key: list0[1]});
      if (val) {
        m_kachery_urls[name] = val;
        return val;
      }
    }
    else return null;
  }

  async function resolve_key_path(path) {
    let a = parse_key_path(path);
    if (!a) return null;
    if (a.location == 'pairio') {
      let val = await that.getValue({key:a.key, hashed_key:a.hashed_key, subkey:a.subkey, collection:a.collection});
      if (!val) return null;
      if ((!val.startsWith('sha1://')) && (!val.startsWith('sha1dir://'))) {
        console.warn('Invalid value when resolving key path', path, val);
        return null;
      }
      if (a.extra_path) {
        val = val + '/' + a.extra_path;
      }
      return val;
    }
    else {
      console.warn('Invalid key path location: ' + a.location);
      return null;
    }
  }
}

// function format_file_size(size_bytes) {
//   var a = 1024;
//   var aa = a * a;
//   var aaa = a * a * a;
//   if (size_bytes > aaa * 3) {
//     return Math.floor(size_bytes / aaa) + ' GB';
//   } else if (size_bytes > aaa) {
//     return Math.floor(size_bytes / (aaa / 10)) / 10 + ' GB';
//   } else if (size_bytes > aa * 3) {
//     return Math.floor(size_bytes / aa) + ' MB';
//   } else if (size_bytes > aa) {
//     return Math.floor(size_bytes / (aa / 10)) / 10 + ' MB';
//   } else if (size_bytes > 10 * a) {
//     return Math.floor(size_bytes / a) + ' KB';
//   } else if (size_bytes > a) {
//     return Math.floor(size_bytes / (a / 10)) / 10 + ' KB';
//   } else {
//     return size_bytes + ' bytes';
//   }
// }

async function http_get_json(url, callback) {
  try {
    let response = await axios.get(url, {responseType: 'json'});
    return response.data;
  }
  catch(err) {
    return null;
  }
}

// async function http_get_text(url, callback) {
//   let buf = await http_get_binary(url, {});
//   if (!buf) return null;
//   let txt='';
//   if ('byteLength' in buf) {
//     txt=String.fromCharCode.apply(null, new Uint8Array(buf));
//   }
//   else {
//     txt = buf.toString('utf8');
//   }
//   return txt;
// }

async function http_get_binary(url, opts) {
  opts = opts || {};
  let headers = {};
  if ((opts.start !== undefined) && (opts.end !== undefined)) {
    headers['range'] = `bytes=${opts.start}-${opts.end-1}`;
  }
  let response;
  try {
    response = await axios.get(url, {
        headers: headers,
        responseType: 'arraybuffer'
      });
  }
  catch(err) {
    return null;
  }
  let buf=response.data;
  // this is super-tricky... it seems there may be a difference in this output depending on whether run in browser or on desktop...
  if ('length' in buf) {
    let buf2=new Int8Array(buf.length);
    for (let i=0; i<buf.length; i++)
      buf2[i]=buf[i];
    buf=buf2.buffer;
  }
  ////////
  return buf;
}

async function http_check(url, callback) {
  let response;
  try {
    response = await axios.head(url);
  }
  catch(err) {
    return false;
  }
  return (response.status == 200);
}

// function is_url(fname_or_url) {
//   return ((fname_or_url.indexOf('http://') == 0) || (fname_or_url.indexOf('https://') == 0));
// }

// function ends_with(str, str2) {
//   return (str.slice(str.length - str2.length) == str2);
// }

function MemoryCache() {
  let m_binary_for_sha1 = {};

  this.getBinaryForSha1 = function(sha1) {
    if (sha1 in m_binary_for_sha1) {
      let a = m_binary_for_sha1[sha1];
      a.timestamp = new Date();
      return a.data;
    }
    else {
      return null;
    }
  }
  this.setBinaryForSha1 = function(sha1, data) {
    if (data.length > 1000000) {
      // don't store it if it is too big
      return;
    }
    m_binary_for_sha1[sha1] = {
      timestamp: new Date(),
      data: data
    };
  }
}

function LocalFileCache(sha1_cache_dir, fs) {
  this.getBinaryForSha1 = async function(sha1) {
    if (!fs) return null;
    if (!sha1_cache_dir) return null;
    const util = require('util');
    let exists = util.promisify(fs.exists);
    let readFile = util.promisify(fs.readFile);
    let fname = `${sha1_cache_dir}/${sha1[0]}/${sha1[1]}${sha1[2]}/${sha1}`;
    let does_exist = await exists(fname);
    if (!does_exist) return null;
    let buf = await readFile(fname);
    return buf;
  }
  this.setBinaryForSha1 = async function(sha1, data) {
    if (!fs) return null;
    if (!sha1_cache_dir) return null;
    const util = require('util');
    let exists = util.promisify(fs.exists);
    let writeFile = util.promisify(fs.writeFile);
    let rename = util.promisify(fs.rename);
    let fname = `${sha1_cache_dir}/${sha1[0]}/${sha1[1]}${sha1[2]}/${sha1}`;
    let does_exist = await exists(fname);
    if (does_exist) return;
    mkdir_if_not_exist(`${sha1_cache_dir}`);
    mkdir_if_not_exist(`${sha1_cache_dir}/${sha1[0]}`);
    mkdir_if_not_exist(`${sha1_cache_dir}/${sha1[0]}/${sha1[1]}${sha1[2]}`);
    let fname_tmp = `${fname}.jstmp.${make_random_id(6)}`;
    await writeFile(fname_tmp, new Buffer(data));
    rename(fname_tmp, fname);
  }

  function mkdir_if_not_exist(path) {
    if (!fs) return null;
    if (!fs.existsSync(path)) {
      fs.mkdirSync(path);
    }
  }
}

function parse_key_path(path) {
  let list0 = path.split('/');
  if (list0.length < 5) return null;
  let location = list0[2];
  let collection = list0[3];
  let key = list0[4];
  let subkey = null;
  let hashed_key = null;
  if (key.indexOf(':') >= 0) {
      vals0 = key.split(':');
      if (vals0.length != 2) return null;
      key = vals0[0];
      subkey = vals0[1];
  }
  if (key.startsWith('~')) {
    hashed_key=key.slice(1);
    key=null;
  }
  let extra_path = list0.slice(5).join('/');
  return {
    location:location,
    collection:collection,
    key:key,
    hashed_key:hashed_key,
    subkey:subkey,
    extra_path:extra_path
  }
}

function make_random_id(num_chars) {
  var text = "";
  var possible = "ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz0123456789";
  for (var i = 0; i < num_chars; i++)
    text += possible.charAt(Math.floor(Math.random() * possible.length));
  return text;
}

function hash_of_string(key) {
  // creating hash object 
  let hash = crypto.createHash('sha1');
  let data = hash.update(key, 'utf-8');
  return data.digest('hex');
}

function hash_of_key(key) {
  if (typeof(key) == "string") {
    return hash_of_string(key);
  }
  else {
    return hash_of_string(stable_stringify(key));
  }
}