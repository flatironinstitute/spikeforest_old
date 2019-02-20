#!/usr/bin/env node

const axios = require('axios');
const fs = require('fs');
const KBucketClient = require(__dirname + '/kbucketclient.js').KBucketClient;

function print_usage() {
  console.info('Usage:');
  console.info('kb-prv-download [filename.prv] [output_file]');
}

var CLP = new CLParams(process.argv);

var prv_fname = CLP.unnamedParameters[0] || '';
var output_fname = CLP.unnamedParameters[1] || '';

if (!prv_fname) {
  print_usage();
  process.exit(-1);
}

if (!ends_with(prv_fname, '.prv')) {
  console.error('Input file must end with .prv');
  process.exit(-1);
}

if (!output_fname) {
  print_usage();
  process.exit(-1);
}

var prv_obj = read_json_file(prv_fname);
if (!prv_obj) {
  console.error('Error reading or parsing json file: ' + prv_fname);
  process.exit(-1);
}

var KBUCKET_URL = CLP.namedParameters['kbucket_url'] || process.env.KBUCKET_URL || 'https://kbucket.flatironinstitute.org';
//var KBUCKET_URL = CLP.namedParameters['kbucket_url'] || process.env.KBUCKET_URL || 'https://kbucket.org';

var KBC = new KBucketClient();
KBC.setKBucketUrl(KBUCKET_URL);
KBC.findFile(prv_obj.original_checksum, {}, function(err, resp) {
  if (err) {
    console.error(err);
    return;
  }
  if (!resp.found) {
    console.error('File not found on kbucket.');
    return;
  }
  download_file(resp.url, output_fname, {
    size: prv_obj.original_size
  },function() {

  });
});

function download_file(url, dest_fname, opts, callback) {
  console.info(`Downloading [${url}] > [${dest_fname}] ...`);
  var bytes_downloaded = 0;
  var bytes_total = opts.size || null;
  var timer = new Date();
  axios.get(url, {
      responseType: 'stream'
    })
    .then(function(response) {
      response.data.on('data', function(data) {
        bytes_downloaded += data.length;
        report_progress(bytes_downloaded, bytes_total);
      });
      var write_stream = fs.createWriteStream(dest_fname + '.downloading_');
      response.data.pipe(write_stream);
      response.data.on('end', function() {
        fs.renameSync(dest_fname + '.downloading_', dest_fname);
        console.info(`Downloaded ${format_file_size(bytes_downloaded)} to ${dest_fname}.`)
        setTimeout(function() { //dont catch an error from execution of callback
          callback(null);
        }, 0);
      });
    })
    .catch(function(err) {
      callback(err.message);
    });

  function report_progress(bytes_downloaded, bytes_total) {
    var elapsed = (new Date()) - timer;
    if (elapsed < 5000) {
      return;
    }
    timer = new Date();
    if (bytes_total) {
      console.info(`Downloaded ${format_file_size(bytes_downloaded)} of ${format_file_size(bytes_total)} ...`)
    } else {
      console.info(`Downloaded ${format_file_size(bytes_downloaded)} ...`);
    }
  }

}

function read_json_file(fname) {
  try {
    var txt = require('fs').readFileSync(fname, 'utf8');
    return JSON.parse(txt);
  } catch (err) {
    return null;
  }
}

function ends_with(str, str2) {
  return (str.slice(str.length - str2.length) == str2);
}

function CLParams(argv) {
  this.unnamedParameters = [];
  this.namedParameters = {};

  var args = argv.slice(2);
  for (var i = 0; i < args.length; i++) {
    var arg0 = args[i];
    if (arg0.indexOf('--') === 0) {
      arg0 = arg0.slice(2);
      var ind = arg0.indexOf('=');
      if (ind >= 0) {
        this.namedParameters[arg0.slice(0, ind)] = arg0.slice(ind + 1);
      } else {
        this.namedParameters[arg0] = '';
        if (i + 1 < args.length) {
          var str = args[i + 1];
          if (str.indexOf('-') != 0) {
            this.namedParameters[arg0] = str;
            i++;
          }
        }
      }
    } else if (arg0.indexOf('-') === 0) {
      arg0 = arg0.slice(1);
      this.namedParameters[arg0] = '';
    } else {
      this.unnamedParameters.push(arg0);
    }
  }
};

function format_file_size(size_bytes) {
  var a = 1024;
  var aa = a * a;
  var aaa = a * a * a;
  if (size_bytes > aaa*3) {
    return Math.floor(size_bytes / aaa) + ' GB';
  } else if (size_bytes > aaa) {
    return Math.floor(size_bytes / (aaa / 10)) / 10 + ' GB';
  } else if (size_bytes > aa*3) {
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