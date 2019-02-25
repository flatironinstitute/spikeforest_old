#!/usr/bin/env node

const fs = require('fs');
const computePrvObject = require(__dirname + '/kbnodeshareindexer.js').computePrvObject;
const computePrvDirectoryObject = require(__dirname + '/kbnodeshareindexer.js').computePrvDirectoryObject;

function print_usage() {
  console.info('Usage:');
  console.info('kb-prv-create [filename]');
  console.info('kb-prv-create [filename] [filename.prv]');
}

var CLP = new CLParams(process.argv);

var fname = CLP.unnamedParameters[0] || '';
var prv_fname_out = CLP.unnamedParameters[1] || '';

if (!fname) {
  print_usage();
  process.exit(-1);
}

if (!require('fs').existsSync(fname)) {
  console.error('Input file does not exist: '+fname);
  process.exit(-1);  
}

var stat0=require('fs').statSync(fname);
if (stat0.isFile()) {
  if ((prv_fname_out)&&(!ends_with(prv_fname_out, '.prv'))) {
    console.error('Output file name must end with .prv');
    process.exit(-1);
  }
  computePrvObject(fname,function(err,obj) {
    if (err) {
      console.error('Error computing prv object: '+err);
      process.exit(-1);
    }
    if (!prv_fname_out) {
      console.info(JSON.stringify(obj,null,4));
      return;
    }
    if (!write_json_file(prv_fname_out,obj)) {
      console.error('Error writing file: '+prv_fname_out);
      process.exit(-1);
    }
  });
}
else if (stat0.isDirectory()) {
  if (!prv_fname_out) {
    console.error('This is a directory, so the output file must be specified.');
    process.exit(-1);
  }
  if (!ends_with(prv_fname_out, '.prvdir')) {
    console.error('Output file for a directory name must end with .prvdir');
    process.exit(-1);
  }
  computePrvDirectoryObject(fname,function(err,obj) {
    if (err) {
      console.error('Error computing prv object: '+err);
      process.exit(-1);
    }
    if (!write_json_file(prv_fname_out,obj)) {
      console.error('Error writing file: '+prv_fname_out);
      process.exit(-1);
    }
  });
}
else {
  console.error('Unexpected problem with stat object.');
  process.exit(-1);
}

function write_json_file(fname,obj) {
  try {
    require('fs').writeFileSync(fname,JSON.stringify(obj,null,4));
    return true;
  }
  catch(err) {
    return false;
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