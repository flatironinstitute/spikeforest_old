exports.SteadyFileIterator = SteadyFileIterator;

const fs = require('fs');
const async = require('async');
const sha1 = require('node-sha1');

function SteadyFileIterator(directory) {
  this.start = function() {
    start();
  };
  this.restart=function() {
    m_files_reported={};
  };
  this.onUpdateFile = function(handler) {
    m_on_update_file_handlers.push(handler);
  };
  this.onRemoveFile = function(handler) {
    m_on_remove_file_handlers.push(handler);
  };

  var m_running = false;
  var m_on_update_file_handlers = [];
  var m_on_remove_file_handlers = [];
  var m_time_between_runs_sec = 3;
  var m_files_found_in_last_iteration = {};
  var m_files_reported = {};

  function start() {
    if (m_running) return;
    m_running = true;
    do_iterate();
  }

  function do_iterate() {
    m_files_found_in_last_iteration = {};
    iterate_directory('', function() {
      for (var relpath in m_files_reported) {
        if (!(relpath in m_files_found_in_last_iteration)) {
          delete m_files_reported[relpath];
          call_on_remove_file_handlers(relpath);
        }
      }
      schedule_next_do_iterate();
    });
  }

  function schedule_next_do_iterate() {
    setTimeout(function() {
      do_iterate();
    }, m_time_between_runs_sec * 1000);
  }

  function include_file_name(name) {
    if (name.startsWith('.')) return false;
    if (name == 'node_modules') return false;
    return true;
  }

  function compute_stat_hash(stat0) {
    var obj = {
      mtime: stat0.mtime + '',
      size: stat0.size
    };
    var str = JSON.stringify(obj);
    return sha1(str);
  }

  function call_on_update_file_handlers(relpath, stat0) {
    for (var i in m_on_update_file_handlers) {
      try {
        m_on_update_file_handlers[i](relpath, stat0);
      } catch (err) {}
    }
  }

  function call_on_remove_file_handlers(relpath) {
    for (var i in m_on_remove_file_handlers) {
      try {
        m_on_remove_file_handlers[i](relpath);
      } catch (err) {}
    }
  }

  function check_file_candidate(relpath, stat0) {
    m_files_found_in_last_iteration[relpath] = true;
    var stat0_hash = compute_stat_hash(stat0);
    var stat_hash = '';
    if (relpath in m_files_reported) {
      stat_hash = m_files_reported[relpath].stat_hash;
    }
    if (stat0_hash != stat_hash) {
      m_files_reported[relpath] = {
        stat_hash: stat0_hash
      };
      call_on_update_file_handlers(relpath, stat0);
    }
  }

  function iterate_directory(reldirpath, callback) {
    const fulldirpath=require('path').join(directory,reldirpath);
    fsafe_readdir(fulldirpath, function(err, list) {
      if (err) {
        console.warn(`Problem reading directory ${fulldirpath}: ${err}`);
        callback(err.message);
        return;
      }

      let steady_timeout=100;

      var subdirs = [];
      async.eachSeries(list, function(item, cb) {
        if ((item == '.') || (item == '..') || (item == '.kbucket')) {
          goto_next();
          return;
        }
        if (!include_file_name(item)) {
          goto_next();
          return;
        }
        var relpath0 = require('path').join(reldirpath, item);
        const fullpath0=require('path').join(directory,relpath0);
        fsafe_stat(fullpath0, function(err0, stat0) {
          if (err0) {
            console.warn(`Error in stat of file ${fullpath0}: ${err0.message}`);
            goto_next();
            return;
          }
          if (stat0.isFile()) {
            check_file_candidate(relpath0, stat0);
          } else if (stat0.isDirectory()) {
            subdirs.push(item);
          } else {
            console.warn(`Item is not a file or a directory: ${item}`);
          }
          goto_next();
        });

        function goto_next() {
          setTimeout(function() {
            cb();
          }, steady_timeout);
        }
      }, iterate_subdirs);

      function iterate_subdirs() {
        async.eachSeries(subdirs, function(subdir, cb) {
          var relpath0 = require('path').join(reldirpath, subdir);
          iterate_directory(relpath0, function() {
            setTimeout(function() {
              cb();
            }, steady_timeout);
          });
        },function() {
          callback();
        });
      }
    });
  }
}

function fsafe_readdir(fullpath, callback) {
  try {
    fs.readdir(fullpath, callback);
  } catch (err) {
    callback('Error in readdir: ' + err.message);
  }
}

function fsafe_stat(fullpath, callback) {
  try {
    fs.stat(fullpath, callback);
  } catch (err) {
    callback('Error in stat: ' + err.message);
  }
}
