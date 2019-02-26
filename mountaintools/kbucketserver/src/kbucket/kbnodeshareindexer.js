exports.KBNodeShareIndexer = KBNodeShareIndexer;
exports.computePrvObject = computePrvObject;
exports.computePrvDirectoryObject = computePrvDirectoryObject;

const fs = require('fs');
const watcher = require('chokidar');
const async = require('async');
const sha1 = require('node-sha1');

const SteadyFileIterator = require(__dirname + '/steadyfileiterator.js').SteadyFileIterator;

function KBNodeShareIndexer(config) {
  let that = this;
  this.startIndexing = function() {
    startIndexing();
  };
  this.restartIndexing = function() {
    m_indexed_files = {};
    m_queued_files = {};
    m_file_iterator.restart();
  };
  this.getPrvForIndexedFile = function(relpath, callback) {
    if (relpath in m_indexed_files) {
      callback(null, m_indexed_files[relpath].prv);
    }
    else {
      compute_prv(relpath,function(err, prv) {
        callback(err, prv);
      });
    }
  };
  this.waitForPrvForIndexedFile = function(relpath, callback) {
    function check_it() {
      if ((relpath in m_indexed_files)) {
        let A = m_indexed_files[relpath];
        if (A.prv) {
          setTimeout(function() {
            callback(null, A.prv);
          }, 1);
          return;
        }
      }
      setTimeout(function() {
        check_it();
      }, 500);
    }
    check_it();
  };
  this.nodeDataForParent = function() {
    var files_by_sha1 = {};
    for (var relpath in m_indexed_files) {
      const file0 = m_indexed_files[relpath];
      const sha1 = file0.prv.original_checksum;
      files_by_sha1[sha1] = {
        path: relpath,
        size: file0.prv.original_size
      };
    }
    m_files_by_sha1=JSON.parse(JSON.stringify(files_by_sha1));
    let ret={
      files_by_sha1: files_by_sha1
    };
    return ret;
  };
  this.findFileBySha1 = function(sha1, callback) {
    console.log('findFileBySha1',sha1);
    console.log('#####',m_files_by_sha1[sha1])
    callback(m_files_by_sha1[sha1] || null);
  }

  var m_queued_files = {};
  var m_indexed_files = {};
  let m_files_by_sha1 = {};
  let m_indexed_something = false;
  let m_prv_cache_manager = new PrvCacheManager(config.configDir(), config.hemlockNodeDirectory());

  var m_file_iterator = new SteadyFileIterator(config.hemlockNodeDirectory());
  m_file_iterator.onUpdateFile(function(relpath, stat0) { //note: stat is not used
    update_file(relpath);
  });
  m_file_iterator.onRemoveFile(function(relpath) {
    remove_file(relpath);
  });

  function update_file(relpath) {
    m_queued_files[relpath] = true;
  }

  function remove_file(relpath) {
    if (relpath in m_queued_files) {
      delete m_queued_files[relpath];
    }
    if (relpath in m_indexed_files) {
      delete m_indexed_files[relpath];
    }
  }

  function startIndexing() {
    m_file_iterator.start();
  }

  loop(); //start the loop
  function loop() {
    do_handle_file_hints(function(err) {
      if (err) {
        console.warn('Problem handling file hints: ' + err);
      }
      do_handle_queued_files(function(err) {
        if (err) {
          console.warn('Problem handling queued files: ' + err);
        }
        setTimeout(function() {
          loop();
          report_changes();
        }, 10);
      });
    });
  }

  let s_last_report = {};

  function report_changes() {
    var report = {
      num_queued_files: Object.keys(m_queued_files).length,
      num_indexed_files: Object.keys(m_indexed_files).length
    };
    if (JSON.stringify(report) != JSON.stringify(s_last_report)) {
      if ((report.num_queued_files === 0) && (m_indexed_something)) {
        console.info(`Indexed ${report.num_indexed_files} files.`);
      }
      s_last_report = report;
    }
  }

  function do_handle_file_hints(callback) {
    let hints_dir=config.hemlockNodeDirectory()+'/sha1-cache/hints';
    if (!fs.existsSync(hints_dir)) {
      callback(null);
      return;
    }
    fs.readdir(hints_dir, function(err, list) {
      if (err) {
        callback(err.message);
        return;
      }
      async.eachSeries(list, function(item, cb) {
        if ((item == '.') || (item == '..')) {
          cb();
          return;
        }
        let hint_fname = hints_dir+'/'+item;
        let hint_obj = read_json_file(hint_fname);
        if (!hint_obj) {
          cb();
          return;
        }
        let relpath=hint_obj['path'];
        if (relpath) {
          let relpath2='sha1-cache/'+relpath;
          console.info('Updating file from hint: '+relpath2);
          update_file(relpath2);
          safe_remove_file(hint_fname);
          cb();
        }
        else {
          cb();
        }
      },function() {
        callback();
      });
    });
  }


  function do_handle_queued_files(callback) {
    var relpaths = Object.keys(m_queued_files);
    async.eachSeries(relpaths, function(relpath, cb) {
      handle_queued_file(relpath, function(err) {
        if (err) {
          //callback(err);
          //return;
        }
        cb();
      });
    }, function() {
      callback();
    });
  }

  function handle_queued_file(relpath, callback) {
    if (!(relpath in m_queued_files)) {
      callback();
      return;
    }

    delete m_queued_files[relpath];

    const fullpath = require('path').join(config.hemlockNodeDirectory(), relpath);
    if (!exists_sync(fullpath)) {
      if (relpath in m_indexed_files) {
        delete m_indexed_files[relpath];
        callback(null);
        return;
      }
    }

    compute_prv(relpath, function(err, prv) {
      if (err) {
        callback(err);
        return;
      }
      m_indexed_something = true;
      m_indexed_files[relpath] = {
        prv: prv
      };
      callback();
    });
  }

  // used previously
  /*
  function filter_file_name_for_cmd(fname) {
    fname = fname.split(' ').join('\\ ');
    fname = fname.split('$').join('\\$');
    return fname;
  }
  */

  function compute_prv(relpath, callback) {
    var prv_obj = m_prv_cache_manager.getPrvFromCache(relpath);
    if (prv_obj) {
      callback(null, prv_obj);
      return;
    }
    const fullpath = require('path').join(config.hemlockNodeDirectory(), relpath);
    //computePrvObject(fullpath, function(err, obj) {
    // Note: it's important to do it like the following, because node-sha1 sometimes crashes (if the file disappears) so we want to separate this into a different process
    if (!require('fs').existsSync(fullpath)) {
      callback('File does not exist: '+fullpath);
      return;
    }

    console.info(`Computing prv for: ${relpath}`);
    run_prv_create(fullpath, function(err,obj) {
      if (err) {
        console.error('Error computing prv ***: '+err);
        callback(err);
        return;
      }
      m_prv_cache_manager.savePrvToCache(relpath, obj);
      callback(null, obj);
    });
  }
}

function run_prv_create(path,callback) {
  run_command_and_read_stdout(__dirname+`/kb-prv-create.js ${path}`,function(err,txt) {
    if (err) {
      callback(err);
      return;
    }
    let obj;
    try {
      obj=JSON.parse(txt.trim());
    }
    catch(err) {
      callback('Error parsing json output of kb-prv-create.js.');
      return;
    }
    callback(null,obj);
  });
}

function run_command_and_read_stdout(cmd, callback) {
  require('child_process').exec(cmd,function(error, stdout, stderr) { 
    if (error) {
      callback(error.message);
      return;
    }
    callback(null,stdout); 
  });
}

function stat_file(fname) {
  try {
    return require('fs').statSync(fname);
  } catch (err) {
    return null;
  }
}

function computePrvDirectoryObject(path0, callback) {
  var ret = {
    files: {},
    dirs: {}
  };
  fs.readdir(path0, function(err, list) {
    if (err) {
      callback(err.message);
      return;
    }
    async.eachSeries(list, function(item, cb) {
      if ((item == '.') || (item == '..') || (item == '.kbucket')) {
        cb();
        return;
      }
      if (!include_file_name(item)) {
        cb();
        return;
      }
      var path1 = require('path').join(path0, item);
      fs.stat(path1, function(err0, stat0) {
        if (err0) {
          callback(`Error in stat of file ${path1}: ${err0.message}`);
          return;
        }
        if (stat0.isFile()) {
          console.info(`Computing prv for ${path1} ...`);
          computePrvObject(path1, function(err1, prv_obj1) {
            if (err1) {
              callback(`Error for file ${path1}: ${err1}`);
              return;
            }
            ret.files[item] = prv_obj1;
            cb();
          });
        } else if (stat0.isDirectory()) {
          computePrvDirectoryObject(path1, function(err1, prvdir_obj1) {
            if (err1) {
              callback(err1);
              return;
            }
            ret.dirs[item] = prvdir_obj1;
            cb();
          });
        } else {
          callback('Error in stat object for file: ' + path1);
          return;
        }
      });
    }, function() {
      callback(null, ret);
    });
  });
}

function computePrvObject(fname, callback) {
  if (!stat_file(fname)) {
    callback('Cannot stat file: ' + fname);
    return;
  }
  compute_file_sha1(fname, {}, function(err, sha1) {
    if (err) {
      callback(err);
      return;
    }
    compute_file_sha1(fname, {
      start_byte: 0,
      end_byte: 999
    }, function(err, sha1_head) {
      if (err) {
        callback(err);
        return;
      }
      var fcs = 'head1000-' + sha1_head;
      var stat1 = stat_file(fname);
      var obj = {        
        original_checksum: sha1,
        original_size: stat1.size,
        original_fcs: fcs,
        original_path: require('path').resolve(fname),
        prv_version: '0.11'
      };
      callback('', obj);
    });
  });
}

function PrvCacheManager(config_dir, node_directory) {
  this.getPrvFromCache = function(relpath) {
    return get_prv_from_cache(relpath);
  };
  this.savePrvToCache = function(relpath, prv) {
    try {
      save_prv_to_cache(relpath, prv);
    }
    catch(err) {
      console.warn(`Warning: problem saving prv to cache (relpath=${relpath}): ${err.message}`);
    }
  };

  if (!require('fs').existsSync(config_dir + '/prv_cache')) {
    require('fs').mkdirSync(config_dir + '/prv_cache');
  }

  function get_prv_cache_fname(path) {
    // used for kbnode_type='share'
    if (!path) return '';
    let fname0=sha1(path).slice(0, 20) + '.json';
    let path1=config_dir + '/prv_cache/'+fname0.slice(0,1);
    let path2=path1+'/'+fname0.slice(1,3);
    if (!require('fs').existsSync(path1)) {
      require('fs').mkdirSync(path1);
    }
    if (!require('fs').existsSync(path2)) {
      require('fs').mkdirSync(path2);
    }
    return path2 + '/'+fname0;
  }

  function get_prv_from_cache(relpath) {
    // used for kbnode_type='share'
    var cache_fname = get_prv_cache_fname(relpath);
    if (!require('fs').existsSync(cache_fname)) {
      return null;
    }
    var obj = read_json_file(cache_fname);
    if (!obj) return null;
    if (!prv_cache_object_matches_file(obj, node_directory + '/' + relpath)) {
      return null;
    }
    return obj.prv;
  }

  function prv_cache_object_matches_file(obj, path) {
    // used for kbnode_type='share'
    if (!obj) return false;
    let stat0;
    try {
      stat0 = require('fs').statSync(path);
    } catch (err) {
      return false;
    }
    if (stat0.size != obj.size) {
      return false;
    }
    if (stat0.mtime + '' != obj.mtime) {
      return false;
    }
    if (!obj.prv) return false;
    return true;
  }

  function save_prv_to_cache(relpath, prv) {
    // used for kbnode_type='share'
    var cache_fname = get_prv_cache_fname(relpath);
    var stat0 = require('fs').statSync(node_directory + '/' + relpath);
    var obj = {};
    obj.path = relpath;
    obj.size = stat0.size;
    obj.mtime = stat0.mtime + '';
    obj.prv = prv;
    write_json_file(cache_fname, obj);
  }

  function start_the_cleaner() {
    cleanup(function(err) {
      if (err) {
        console.error(err);
        console.error('Aborting');
        process.exit(-1);
        return;
      }
      setTimeout(start_the_cleaner, 60 * 1000);
    });
  }

  function cleanup(callback) {
    let prv_cache_dir = config_dir + '/prv_cache';
    cleanup_prv_cache(prv_cache_dir, function() {
      callback(null);
    });
  }

  function cleanup_prv_cache(prv_cache_dir, callback) {
    // used for kbnode_type='share'
    require('fs').readdir(prv_cache_dir, function(err, files) {
      if (err) {
        callback('Error in cleanup_prv_cache:readdir: ' + err.message);
        return;
      }
      async.eachSeries(files, function(file, cb) {
        let stat0 = stat_file(prv_cache_dir+'/'+file);
        if (!stat0) {
          cb();
          return;
        }
        if (stat0.isFile()) {
          cleanup_prv_cache_file(prv_cache_dir + '/' + file, function(err) {
            if (err) {
              callback(err);
              return;
            }
            cb();
          });
        }
        else if (stat0.isDirectory()) {
          cleanup_prv_cache(prv_cache_dir + '/' + file, function(err) {
            if (err) {
              callback(err);
              return;
            }
            cb();
          });
        }
        else {
          cb();
        }
      }, function() {
        callback();
      });
    });
  }

  function cleanup_prv_cache_file(cache_filepath, callback) {
    // used for kbnode_type='share'
    var obj = read_json_file(cache_filepath);
    if (!obj) {
      safe_remove_file(cache_filepath);
      callback(null);
      return;
    }
    var relpath1 = obj.path;
    if (get_prv_cache_fname(relpath1) != cache_filepath) {
      safe_remove_file(cache_filepath);
      callback(null);
      return;
    }
    if (!prv_cache_object_matches_file(obj, node_directory + '/' + relpath1)) {
      safe_remove_file(cache_filepath);
      callback(null);
      return;
    }
    callback(null);
  }

  start_the_cleaner();
}

function safe_remove_file(filepath) {
  try {
    require('fs').unlinkSync(filepath);
  } catch (err) {
    console.warn('Unable to remove file: ' + filepath);
  }
}

function compute_file_sha1(path, opts, callback) {
  var opts2 = {};
  if (opts.start_byte) opts2.start = opts.start_byte;
  if (opts.end_byte) opts2.end = opts.end_byte;
  try {
    var stream = require('fs').createReadStream(path, opts2);
  }
  catch(err) {
    callback('Error creating read stream for file: '+path);
    return;
  }
  try {
    sha1(stream, function(err, hash) {
      if (err) {
        console.error(err);
        callback('Error:---: ' + err);
        return;
      }
      callback(null, hash);
    });
  }
  catch(err) {
    callback('Error (*): '+err.mesage);
  }
}

function include_file_name(name) {
  if (name.startsWith('.')) return false;
  if (name == 'node_modules') return false;
  return true;
}

function exists_sync(path) {
  try {
    return require('fs').existsSync(path);
  } catch (err) {
    return false;
  }
}

function parse_json(str) {
  try {
    return JSON.parse(str);
  } catch (err) {
    return null;
  }
}

function read_json_file(fname) {
  try {
    var txt = require('fs').readFileSync(fname, 'utf8');
    return parse_json(txt);
  } catch (err) {
    return null;
  }
}

function read_text_file(fname) {
  try {
    var txt = require('fs').readFileSync(fname, 'utf8');
    return txt;
  } catch (err) {
    return null;
  }
}

function write_text_file(fname, txt) {
  try {
    require('fs').writeFileSync(fname, txt);
    return true;
  } catch (err) {
    return false;
  }
}

function write_json_file(fname, obj) {
  try {
    require('fs').writeFileSync(fname, JSON.stringify(obj, null, 4));
    return true;
  } catch (err) {
    return false;
  }
}