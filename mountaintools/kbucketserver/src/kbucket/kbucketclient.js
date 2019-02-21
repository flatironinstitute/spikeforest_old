exports.KBucketClient = KBucketClient;

var axios = require('axios');
var async = require('async');

var s_kbucket_client_data = {
  infos_by_sha1: {}
}

function KBucketClient() {
  this.setKBucketUrl = function(url) {
    m_kbucket_url = url;
  };
  this.findFile = function(sha1, opts, callback) {
    findFile(sha1, opts, callback);
  }
  this.clearCacheForFile = function(sha1) {
    clearCacheForFile(sha1);
  };
  this.clearCache = function() {
    s_kbucket_client_data.infos_by_sha1 = {};
  };
  this.getNodeInfo = function(kbnode_id, callback) {
    getNodeInfo(kbnode_id, callback);
  };
  this.readDir = function(kbnode_id, subdirectory, callback) {
    readDir(kbnode_id, subdirectory, callback);
  }

  //var m_kbucket_url='https://kbucket.org';
  var m_kbucket_url = 'https://kbucket.flatironinstitute.org';

  function clearCacheForFile(sha1) {
    if (sha1 in s_kbucket_client_data.infos_by_sha1) {
      delete s_kbucket_client_data.infos_by_sha1[sha1];
    }
  }

  function findFile(sha1, opts, callback) {
    if (typeof(opts) == 'string') {
      opts = {
        filename: opts
      };
    }
    find_file(sha1, opts, function(err, resp) {
      if (err) {
        callback(err);
        return;
      }
      if (resp.found) {
        callback(null, resp);
        return;
      }
      if (resp.alt_hub_url) { // where is this set??
        var opts2 = JSON.parse(JSON.stringify(opts));
        opts2.kbucket_url = resp.alt_hub_url;
        find_file(sha1, opts2, callback);
        return;
      }
      callback(null, resp);
    });
  }

  function find_file(sha1, opts, callback) {
    // look for file locally first?
      
    // look-up has already been done.
    if (s_kbucket_client_data.infos_by_sha1[sha1]) {
      callback(null, s_kbucket_client_data.infos_by_sha1[sha1]);
      return;
    }
    // No kbucket url to initialize tree search
    if (!m_kbucket_url) {
      callback('KBucketClient: kbucket url not set.');
      return;
    }
    var url0 = opts.kbucket_url || m_kbucket_url;
    var url1 = url0 + '/find/' + sha1;
    if (opts.filename) {
      url1 += '/' + opts.filename;
    }
    // Query kbucket to match the sha1 hash
    http_get_json(url1, function(err, obj) {
      if (err) {
        callback(`Error in http_get_json (${url1}): ` + err, null);
        return;
      }
      if (!obj.found) {
        callback(null, obj);
        return;
      }
      var url = '';
      var candidate_urls = obj.urls || [];
      //there could be multiple candidate urls to choose.
      //should this be done in series or parallel?
      async.eachSeries(candidate_urls, function(candidate_url, cb) {
        url_exists(candidate_url, function(exists) {
          if (exists) {
            url = candidate_url;
            finalize();
            return;
          }
          cb();
        })
      }, function() {
        finalize();
      });

      function finalize() {
        if (!url) {
          console.warn('Found file, but none of the urls actually work.', candidate_urls);
          callback(null, {
            found: false
          });
          return;
        }
        var info0 = {
          found: true,
          url: url,
          size: obj.size
        };
        s_kbucket_client_data.infos_by_sha1[sha1] = info0;
        callback(null, info0);
      }
    });
  }

  function getNodeInfo(kbnode_id, callback) {
    var url0 = `${m_kbucket_url}/${kbnode_id}/api/nodeinfo`;
    http_get_json(url0, function(err, resp) {
      if (err) {
        callback(err);
        return;
      }
      if (!resp.info) {
        callback('No info field in response to nodeinfo.');
        return;
      }
      callback(err, resp.info);
    });
  }

  function readDir(kbnode_id, subdirectory, callback) {
    var url0 = `${m_kbucket_url}/${kbnode_id}/api/readdir/${subdirectory}`;
    http_get_json(url0, function(err, resp) {
      if (err) {
        callback(err);
        return;
      }
      if (resp.error) {
        callback(resp.error);
        return;
      }
      callback(null, resp.files, resp.dirs);
    });
  }
}

function http_get_json(url, callback) {
  axios.get(url, {
      responseType: 'json'
    })
    .then(function(response) {
      setTimeout(function() { // so we don't catch an error from the timeout
        callback(null, response.data);
      }, 0);
    })
    .catch(function(error) {
      callback(error.message);
    });
}

function url_exists(url, callback) {
  axios.head(url)
    .then(function(response) {
      setTimeout(function() { // so we don't catch an error from the timeout
        callback(response.status == 200);
      }, 0);
    })
    .catch(function(error) {
      callback(false);
    });
}
