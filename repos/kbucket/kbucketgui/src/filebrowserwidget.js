exports.FileBrowserWidget = FileBrowserWidget;

const download = require('downloadjs');
const async = require('async');

function FileBrowserWidget() {
  var that = this;

  this.element = function() {
    return m_element;
  };
  this.on = function(name, callback) {
    m_element.on(name, callback);
  };
  this.setKBHubUrl = function(url) {
    if (m_kbhub_url == url) return;
    m_kbhub_url = url;
    refresh();
  };
  this.setKBShareId = function(id) {
    if (m_kbshare_id == id) return;
    m_kbshare_id = id;
    refresh();
  };
  this.setCurrentDirectory = function(path) {
    if (m_current_directory == path) return;
    m_current_directory = path;
    refresh();
  };
  this.setRootLabel = function(label) {
    m_root_label = label;
    refresh();
  };

  var m_element = $(`
		<span>
			<div id=path style="padding-bottom:20px"></div>
			<table class=table id=files_table></table>
		</span>
	`);
  var m_files_table = m_element.find('#files_table');
  var m_kbhub_url = '';
  var m_kbshare_id = '';
  var m_current_directory = '';
  let m_root_label = 'ROOT';

  let global_refresh_code = 0;
  refresh();

  function refresh() {
    global_refresh_code++;
    let local_refresh_code = global_refresh_code;
    if ((!m_kbshare_id) || (!m_kbhub_url)) {
      m_element.find('#path').html('');
      m_files_table.empty();
      return;
    }
    var path_element = create_path_element();
    m_element.find('#path').empty();
    m_element.find('#path').append(path_element);
    m_files_table.empty();
    m_files_table.append(`<tr><th style="width:100px">Name</th><th>Size</th><th>PRV</th><th>SHA-1</th></tr>`);
    readdir(m_current_directory, {}, function(err, files, dirs) {
      if (local_refresh_code != global_refresh_code)
        return; // somebody else is refreshing the view
      if (err) {
        throw err;
      }
      for (var i in dirs) {
        var row = $('<tr></tr>');
        row.append('<td id=name></td>')
        row.append('<td id=size></td>')
        row.append('<td id=prv></td>')
        row.append('<td id=sha1></td>')
        row.dir = dirs[i];
        m_files_table.append(row);
        update_dir_row(row);
      }
      for (var i in files) {
        var row = $('<tr></tr>');
        row.append('<td id=name></td>')
        row.append('<td id=size></td>')
        row.append('<td id=prv></td>')
        row.append('<td id=sha1></td>')
        row.file = files[i];
        m_files_table.append(row);
        update_file_row(row);
      }
    });
  }

  function readdir(directory, opts, callback) {
    var url0 = `${m_kbhub_url}/${m_kbshare_id}/api/readdir/${directory}`;
    $.getJSON(url0, function(resp) {
      if (resp.error) {
        callback(resp.error);
        return;
      }
      callback(null, resp.files, resp.dirs);
    });
  }

  function create_path_element() {
    var path_element = $('<span />');
    path_element.append(`<a href=# data-path="">${m_root_label}</a>`);
    var aaa = m_current_directory.split('/');
    var path0 = '';
    for (var i in aaa) {
      if (aaa[i]) {
        path0 = require('path').join(path0, aaa[i]);
        path_element.append('/');
        path_element.append(`<a href=# data-path="${path0}">${aaa[i]}</a>`);
      }
    }
    path_element.find('a').click(function() {
      var path0 = $(this).attr('data-path')
      that.setCurrentDirectory(path0);
    });
    return path_element;
  }

  function update_dir_row(row) {
    var dir = row.dir;
    var link = $('<a href=#></a>');
    link.html(dir.name);
    link.click(function() {
      var path = require('path').join(m_current_directory, dir.name);
      that.setCurrentDirectory(path);
    });
    row.find('#name').empty();
    row.find('#name').append('<span class="octicon octicon-file-directory"></span>&nbsp;');
    row.find('#name').append(link);
    row.find('#size').html('.');
    row.find('#sha1').html('.'); {
      var prvdir_link = create_prvdir_link(dir.name, m_current_directory);
      row.find('#prv').append(prvdir_link);
    }
  }

  function update_file_row(row) {
    var file = row.file;
    var link = $('<a></a>');
    link.html(file.name);
    link.attr('target', '_blank');
    var filepath = require('path').join(m_current_directory, file.name);
    var url = `${m_kbhub_url}/${m_kbshare_id}/download/${filepath}`;
    link.attr('href', url);
    row.find('#name').empty();
    row.find('#name').append('<span class="octicon octicon-file"></span>&nbsp;');
    row.find('#name').append(link);
    row.find('#size').html(format_file_size(file.size));
    if (file.prv) {
      var prv_link = create_prv_link(file.name, file.prv)
      row.find('#prv').append(prv_link);
      var sha1_elmt = $(`<span>${file.prv.original_checksum}</span>`)
      row.find('#sha1').append(sha1_elmt);
    } else {
      var sha1_elmt = $('<span>[Not yet indexed]</span>');
      row.find('#sha1').append(sha1_elmt);
    }
  }

  function create_prv_link(fname, prv) {
    var elmt = $(`<a href=#>${fname}.prv</a>`);
    elmt.attr('title', `Download ${fname}.prv`);
    elmt.click(function() {
      var json = JSON.stringify(prv, null, 4);
      download(json, fname + '.prv');
    });
    return elmt;
  }

  function create_prvdir_link(dirname, current_directory) {
    var elmt = $(`<span><a id=prepare href=#>Prepare .prvdir</a> <span id=download></span></span>`);
    elmt.find('#prepare').attr('title', `Prepare download of ${dirname}.prvdir`);
    elmt.find('#prepare').click(function() {
      elmt.find('#download').html('Preparing...');
      create_prvdir_object(dirname, current_directory, {
        status_elmt: elmt.find('#download')
      }, function(err, obj) {
        if (err) {
          elmt.find('#download').html('Error: ' + err);
          return;
        }

        var download_link = $('<a href=#>(download)</a>');
        download_link.attr('title', `Download ${dirname}.prvdir`)
        download_link.click(function() {
          var json = JSON.stringify(obj, null, 4);
          download(json, dirname + '.prvdir');
        });
        elmt.find('#download').empty();
        elmt.find('#download').append(download_link);
      });
    });
    return elmt;
  }

  function create_prvdir_object(dirname, current_directory, opts, callback) {
    var obj = {
      files: {},
      dirs: {}
    };
    if (opts.status_elmt) {
      opts.status_elmt.html('Reading directory: ' + dirname);
    }
    readdir(require('path').join(current_directory, dirname), {}, function(err, files, dirs) {
      if (err) {
        callback(err);
        return;
      }
      for (var i in files) {
        var file0 = files[i];
        if (!file0.prv) {
          callback('Not all files have been indexed.');
          return;
        }
        obj['files'][file0.name] = file0.prv;
      }
      async.eachSeries(dirs, function(dir0, cb) {
        create_prvdir_object(dir0.name, require('path').join(current_directory, dirname), opts, function(err, obj0) {
          if (err) {
            callback(err);
            return;
          }
          obj['dirs'][dir0.name] = obj0;
          cb();
        })
      }, function() {
        callback(null, obj);
      });
    });
  }

  function shorten_key(key, num) {
    return key.slice(0, num) + '...';
  }
}

function format_file_size(size_bytes) {
  var a = 1024;
  var aa = a * a;
  var aaa = a * a * a;
  if (size_bytes > aaa) {
    return Math.floor(size_bytes / aaa) + ' GB';
  } else if (size_bytes > aaa) {
    return Math.floor(size_bytes / (aaa / 10)) / 10 + ' GB';
  } else if (size_bytes > aa) {
    return Math.floor(size_bytes / aa) + ' MB';
  } else if (size_bytes > aa) {
    return Math.floor(size_bytes / (aa / 10)) / 10 + ' MB';
  } else if (size_bytes > 10 * a) {
    return Math.floor(size_bytes / a) + ' KB';
  } else if (size_bytes > a) {
    return Math.floor(size_bytes / (a / 10)) / 10 + ' KB';
  } else {
    return size_bytes + ' bytes';
  }
}