#!/usr/bin/env node

const fs = require('fs');
const KBucketClient = require(__dirname + '/kbucketclient.js').KBucketClient;

function print_usage() {
  console.info('Usage:');
  console.info('kb-prv-find [filename.prv]');
}

var CLP = new CLParams(process.argv);

var prv_fname = CLP.unnamedParameters[0] || '';

if (!prv_fname) {
  print_usage();
  process.exit(-1);
}

if (!ends_with(prv_fname, '.prv')) {
  console.error('Input file must end with .prv');
  process.exit(-1);
}

var prv_obj = read_json_file(prv_fname);
if (!prv_obj) {
  console.error('Error reading or parsing json file: ' + prv_fname);
  process.exit(-1);
}

//var KBUCKET_URL = CLP.namedParameters['kbucket_url'] || process.env.KBUCKET_URL || 'https://kbucket.org';
var KBUCKET_URL = CLP.namedParameters['kbucket_url'] || process.env.KBUCKET_URL || 'https://kbucket.flatironinstitute.org';

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
  console.info(resp.url);
});

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