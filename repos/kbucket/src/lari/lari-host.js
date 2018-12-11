#!/usr/bin/env node

const fs = require('fs');

const HemlockNode = require(__dirname + '/../hemlock/hemlocknode.js').HemlockNode;
const LariHttpServer = require(__dirname + '/larihttpserver.js').LariHttpServer;
const LariNodeApi = require(__dirname + '/larinodeapi.js').LariNodeApi;
const KBHttpServer = require(__dirname + '/../kbucket/kbhttpserver.js').KBHttpServer;
const KBNodeApi = require(__dirname + '/../kbucket/kbnodeapi.js').KBNodeApi;
const KBNodeShareIndexer = require(__dirname + '/../kbucket/kbnodeshareindexer.js').KBNodeShareIndexer;
const HemlockNodeConfig = require(__dirname + '/../hemlock/hemlocknodeconfig.js').HemlockNodeConfig;
const copyFileSync = require('fs-copy-file-sync')
const list_processors=require(__dirname+'/larijobmanager.js').list_processors;

var CLP = new CLParams(process.argv);

var node_directory = CLP.unnamedParameters[0] || '.';
node_directory = require('path').resolve(node_directory);
if (!fs.existsSync(node_directory)) {
  console.error('Directory does not exist: ' + node_directory);
  process.exit(-1);
}
if (!fs.statSync(node_directory).isDirectory()) {
  console.error('Not a directory: ' + node_directory);
  process.exit(-1);
}

process.env.ML_TEMPORARY_DIRECTORY=node_directory+'/.tmp';
process.env.ML_CONFIG_DIRECTORY=node_directory+'/.mountainlab';
if (!fs.existsSync(process.env.ML_CONFIG_DIRECTORY)) {
  fs.mkdirSync(process.env.ML_CONFIG_DIRECTORY);
}
if (!fs.existsSync(process.env.ML_CONFIG_DIRECTORY+'/packages')) {
  fs.mkdirSync(process.env.ML_CONFIG_DIRECTORY+'/packages');
}

let lari_context=null;

initialize_lari(function() {
  copy_config_from_lari_to_kbucket(function() {
    setTimeout(function() {
      initialize_kbucket();  
    },1000);
  });
});

function initialize_lari(callback) {
  var init_opts = {};
  if ('auto' in CLP.namedParameters) {
    init_opts.auto_use_defaults = true;
  }
  init_opts.config_directory_name = '.lari';
  init_opts.config_file_name = 'larinode.json';
  init_opts.node_type_label = 'leaf';
  init_opts.network_type = 'lari';

  var X = new HemlockNode(node_directory, 'leaf');
  let context = X.context();
  let API = new LariNodeApi(context);
  let SS = new LariHttpServer(API);
  X.setHttpServer(SS.app());
  let TM = new LeafManager();
  X.setLeafManager(TM);
  X.initialize(init_opts, function(err) {
    if (err) {
      console.error(err);
      process.exit(-1);
    }
    lari_context=context;
    callback();
  });
  do_get_spec();
  function do_get_spec() {
    list_processors(function(err) {
      if (err) {
        console.warn('Problem in list processors: '+err);
      }
      setTimeout(function() {
        do_get_spec();
      },6000);
    });
  }
}

function copy_config_from_lari_to_kbucket(callback) {
  if (!fs.existsSync(node_directory+'/.kbucket'))
    fs.mkdirSync(node_directory+'/.kbucket');
  let opts_kbucket={
    config_directory_name:'.kbucket',
    config_file_name:'kbnode.json',
    network_type:'kbucket'
  };
  let kbucket_config=new HemlockNodeConfig(node_directory,opts_kbucket);

  let opts_lari={
    config_directory_name:'.lari',
    config_file_name:'larinode.json',
    network_type:'lari'
  };
  let lari_config=new HemlockNodeConfig(node_directory,opts_lari);

  let fields_to_copy=[
    'node_type','node_id','name','scientific_research','description','owner','owner_email','confirm_share'
  ];

  for (let i in fields_to_copy) {
    let key=fields_to_copy[i];
    kbucket_config.setConfig(key,lari_config.getConfig(key));
  }
  kbucket_config.setConfig('network_type','kbucket');

  if (fs.existsSync(node_directory+'/.kbucket/public.pem')) {
    if (kbucket_config.publicKey()!=lari_config.publicKey()) {
      console.error('Public keys do not match between kbucket and lari configuration. Aborting.');
      process.exit(-1);
    }
  }

  copyFileSync(node_directory+'/.lari/private.pem',node_directory+'/.kbucket/private.pem');
  copyFileSync(node_directory+'/.lari/public.pem',node_directory+'/.kbucket/public.pem');
  callback();
}

function initialize_kbucket() {
  var init_opts = {};
  if ('auto' in CLP.namedParameters) {
    init_opts.auto_use_defaults = true;
  }
  init_opts.config_directory_name = '.kbucket';
  init_opts.config_file_name = 'kbnode.json';
  init_opts.node_type_label = 'share';
  init_opts.network_type = 'kbucket';

  var X = new HemlockNode(node_directory, 'leaf');
  let context = X.context();
  let API = new KBNodeApi(context);
  let SS = new KBHttpServer(API);
  X.setHttpServer(SS.app());
  let TM = new LeafManager();
  X.setLeafManager(TM);
  X.initialize(init_opts, function(err) {
    if (err) {
      console.error(err);
      process.exit(-1);
    }
    context.share_indexer = new KBNodeShareIndexer(context.config);
    lari_context.share_indexer=context.share_indexer;
    lari_context.kbucket_url=context.config.getConfig('parent_hub_url');
    context.share_indexer.startIndexing();
  });

  function LeafManager() {
    this.nodeDataForParent = function() {
      return context.share_indexer.nodeDataForParent();
    };
    this.restart = function() {
      console.info('Restarting indexing.');
      if (context.share_indexer) {
        context.share_indexer.restartIndexing();
      }
    };
  }
}

function LeafManager() {
  this.nodeDataForParent = function() {
    return {};
  };
  this.restart = function() {};
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
}
