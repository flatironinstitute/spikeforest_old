exports.KBNode = KBNode;

const async = require('async');
const express = require('express');
const cors = require('cors');
const WebSocket = require('ws');
const findPort = require('find-port');
const fs = require('fs');
const axios = require('axios');
const jsondiffpatch = require('jsondiffpatch');
//const REQUEST = require('request');

const logger = require(__dirname + '/logger.js').logger();
const KBNodeConfig = require(__dirname + '/kbnodeconfig.js').KBNodeConfig;
const KBNodeShareIndexer = require(__dirname + '/kbnodeshareindexer.js').KBNodeShareIndexer;
//const HttpOverWebSocketServer = require(__dirname + '/httpoverwebsocket.js').HttpOverWebSocketServer;
const KBConnectionToChildNode = require(__dirname + '/kbconnectiontochildnode.js').KBConnectionToChildNode;
const KBConnectionToParentHub = require(__dirname + '/kbconnectiontoparenthub.js').KBConnectionToParentHub;
const KBucketHubManager = require(__dirname + '/kbuckethubmanager.js').KBucketHubManager;
const PoliteWebSocket = require(__dirname + '/politewebsocket.js').PoliteWebSocket;
const KBucketClient = require(__dirname + '/kbucketclient.js').KBucketClient;
const KBNodeApi = require(__dirname + '/kbnodeapi.js').KBNodeApi;

// TODO: think of a better default range
const KBUCKET_SHARE_PORT_RANGE = process.env.KBUCKET_SHARE_PORT_RANGE || '2000-3000';
const KBUCKET_SHARE_HOST = process.env.KBUCKET_SHARE_HOST = 'localhost';

function KBNode(kbnode_directory, kbnode_type) {
  this.initialize = function(opts, callback) {
    initialize(opts, callback);
  };
  this.setKBucketUrl = function(url) {
    m_kbucket_url = url;
  };

  const m_config = new KBNodeConfig(kbnode_directory);
  let m_context = {};
  let m_last_node_data_reported = null;
  var API = new KBNodeApi(m_config, m_context);
  var m_app = null;
  m_context.connection_to_parent_hub = null;
  var m_kbucket_url = 'https://kbucket.flatironinstitute.org';

  // only used for kbnode_type='share'
  m_context.share_indexer = null;
  if (kbnode_type == 'share')
    m_context.share_indexer = new KBNodeShareIndexer(m_config);

  // only used for kbnode_type='hub'
  m_context.hub_manager = null;
  if (kbnode_type == 'hub')
    m_context.hub_manager = new KBucketHubManager(m_config);

  function initialize(opts, callback) {
    var steps = [];

    // for both types
    steps.push(create_config_if_needed);
    steps.push(generate_pem_keys_and_id_if_needed);
    steps.push(initialize_config);
    steps.push(run_interactive_config);
    if (!opts.clone_only) {
      steps.push(start_http_server);
    }

    // for kbnode_type='hub'
    if (kbnode_type == 'hub') {
      steps.push(start_websocket_server);
    }

    // for both types
    if (!opts.clone_only) {
      steps.push(connect_to_parent_hub);
      steps.push(start_sending_node_data_to_parent);
    }

    if (!opts.clone_only) {
      steps.push(start_checking_config_exists);
    }

    // for kbnode_type='share'
    if (kbnode_type == 'share') {
      if (!opts.clone_only) {
        steps.push(start_indexing);
      }
      if (opts.clone_only) {
        steps.push(download_for_clone);
      }
    }

    async.series(steps, function(err) {
      callback(err);
    });

    function run_interactive_config(callback) {
      m_config.runInteractiveConfiguration(opts, callback);
    }

    function create_config_if_needed(callback) {
      if (!m_config.configDirExists()) {
        console.info(`Creating kbucket ${kbnode_type} configuration in ${m_config.kbNodeDirectory()}/.kbucket ...`);
        m_config.createNew(kbnode_type, opts, function(err) {
          if (err) {
            callback(err);
            return;
          }
          callback(null);
        });
      } else {
        callback(null);
      }
    }

    function generate_pem_keys_and_id_if_needed(callback) {
      var private_key_fname = m_config.configDir() + '/private.pem';
      var public_key_fname = m_config.configDir() + '/public.pem';
      if ((!fs.existsSync(public_key_fname)) && (!fs.existsSync(private_key_fname))) {
        console.info('Creating private/public keys ...');
        m_config.generatePemFilesAndId(opts, function(err) {
          if (err) {
            callback(err);
            return;
          }
          callback(null);
        });
      } else {
        callback(null);
      }
    }

    function download_for_clone(callback) {
      do_download_for_clone(opts, opts.kbshare_subdirectory || '', '', function(err) {
        callback(err);
      });
    }
  }

  function initialize_config(callback) {
    console.info('Initializing configuration...');
    m_config.initialize(function(err) {
      if (err) {
        callback(err);
        return;
      }
      require(__dirname + '/logger.js').initialize({
        application: 'kbnode',
        directory: m_config.configDir() + '/logs'
      });
      if (m_config.kbNodeType() != kbnode_type) {
        callback('Incorrect type for kbnode: ' + m_config.kbNodeType());
        return;
      }
      callback(null);
    });
  }

  function start_http_server(callback) {
    m_app = express();
    var app = m_app;

    app.set('json spaces', 4); // when we respond with json, this is how it will be formatted

    app.use(cors());

    // API readdir
    app.get('/:kbshare_id/api/readdir/:subdirectory(*)', function(req, res) {
      var params = req.params;
      API.handle_readdir(params.kbshare_id, params.subdirectory, req, res);
    });
    app.get('/:kbshare_id/api/readdir/', function(req, res) {
      var params = req.params;
      API.handle_readdir(params.kbshare_id, '', req, res);
    });

    // API nodeinfo
    app.get('/:kbnode_id/api/nodeinfo', function(req, res) {
      var params = req.params;
      API.handle_nodeinfo(params.kbnode_id, req, res);
    });

    // API download
    app.get('/:kbshare_id/download/:filename(*)', function(req, res) {
      var params = req.params;
      API.handle_download(params.kbshare_id, params.filename, req, res);
    });

    // API prv
    app.get('/:kbshare_id/prv/:filename(*)', function(req, res) {
      var params = req.params;
      API.handle_prv(params.kbshare_id, params.filename, req, res);
    });

    // API find (only for kbnode_type='hub')
    app.get('/find/:sha1/:filename(*)', function(req, res) {
      var params = req.params;
      API.handle_find(params.sha1, params.filename, req, res);
    });
    app.get('/find/:sha1/', function(req, res) {
      var params = req.params;
      API.handle_find(params.sha1, '', req, res);
    });

    get_listen_port(function(err, listen_port) {
      if (err) {
        callback(err);
        return;
      }
      app.port = listen_port;
      m_config.setListenPort(listen_port);

      if (process.env.SSL != null ? process.env.SSL : listen_port % 1000 == 443) {
        // The port number ends with 443, so we are using https
        app.USING_HTTPS = true;
        app.protocol = 'https';
        // Look for the credentials inside the encryption directory
        // You can generate these for free using the tools of letsencrypt.org
        const options = {
          key: fs.readFileSync(__dirname + '/encryption/privkey.pem'),
          cert: fs.readFileSync(__dirname + '/encryption/fullchain.pem'),
          ca: fs.readFileSync(__dirname + '/encryption/chain.pem')
        };

        // Create the https server
        app.server = require('https').createServer(options, app);
      } else {
        app.protocol = 'http';
        // Create the http server and start listening
        app.server = require('http').createServer(app);
      }
      // start listening
      logger.info('Starting http server.', {
        port: app.port,
        protocol: app.protocol,
        kbnode_type: kbnode_type
      });
      app.server.listen(listen_port, function() {
        console.info(`kbucket-${kbnode_type} is running ${app.protocol} on port ${app.port}`);
        callback(null);
      });
    });
  }

  function get_node_data_for_parent() {
    if (m_config.kbNodeType() == 'hub') {
      return m_context.hub_manager.nodeDataForParent();
    } else if (m_config.kbNodeType() == 'share') {
      return m_context.share_indexer.nodeDataForParent();
    } else {
      return {};
    }
  }

  function connect_to_parent_hub(callback) {
    var opts = {
      retry_timeout_sec: 4,
      retry2_timeout_sec: 10
    };
    do_connect_to_parent_hub(opts, function(err) {
      if (err) {
        setTimeout(function() {
          console.error('Connection to parent hub failed: ' + err);
          console.info(`Trying again in ${opts.retry_timeout_sec} seconds`);
          connect_to_parent_hub(callback);
        }, opts.retry_timeout_sec * 1000);
        return;
      }
      callback(null);
    });
  }

  function do_connect_to_parent_hub(opts, callback) {
    var parent_hub_url = m_config.getConfig('parent_hub_url');
    if ((!parent_hub_url) || (parent_hub_url == '.')) {
      if (kbnode_type == 'share') {
        callback('No parent hub url specified.');
      } else {
        callback(null);
      }
      return;
    }
    m_context.connection_to_parent_hub = new KBConnectionToParentHub(m_config);
    m_context.connection_to_parent_hub.onClose(function() {
      m_last_node_data_reported = null;
      m_context.connection_to_parent_hub = null;
      if (opts.retry_timeout_sec) {
        var logmsg = `Connection to parent hub closed. Will retry in ${opts.retry_timeout_sec} seconds...`;
        logger.info(logmsg);
        console.info(logmsg);
        setTimeout(function() {
          retry_connect_to_parent_hub(opts);
        }, opts.retry_timeout_sec * 1000);
      }
    });

    /////////////////////////////////////////////////////////////////////////////////////
    console.info('Connecting to parent hub: ' + parent_hub_url);
    logger.info('Attempting to connect to parent hub', {
      opts: opts
    });
    /////////////////////////////////////////////////////////////////////////////////////

    m_context.connection_to_parent_hub.initialize(parent_hub_url, function(err) {
      if (err) {
        callback(err);
        return;
      }
      if (m_context.share_indexer) {
        m_context.share_indexer.restartIndexing();
      }
      callback(null);
    });
  }

  function retry_connect_to_parent_hub(opts) {
    do_connect_to_parent_hub(opts, function(err) {
      if (err) {
        console.error(err);
        if (opts.retry2_timeout_sec) {
          var logmsg = `Failed to reconnect to parent hub. Will retry in ${opts.retry2_timeout_sec} seconds...`;
          logger.info(logmsg);
          console.info(logmsg);
          setTimeout(function() {
            retry_connect_to_parent_hub(opts);
          }, opts.retry2_timeout_sec * 1000);
        }
      }
    });
  }

  function do_download_for_clone(opts, src_subdirectory, dst_subdirectory, callback) {
    var dirpath0 = require('path').join(kbnode_directory, dst_subdirectory);
    if (dst_subdirectory != '') {
      if (fs.existsSync(dirpath0)) {
        callback('Stopping download for clone. Directory already exists: ' + dirpath0);
        return;
      }
      fs.mkdirSync(dirpath0);
    }
    readdir(src_subdirectory, function(err, files, dirs) {
      if (err) {
        callback(err);
        return;
      }
      async.series([function(cb2) {
        async.eachSeries(files, function(file0, cb) {
          if (!file0.prv) {
            callback(`Stopping download for clone. File not yet indexed: ${src_subdirectory}/${file0.name}`);
            return;
          }
          if (file0.prv.original_size <= opts.max_file_download_size_mb * (1024 * 1024)) {
            _download();
          } else {
            _write_prv();
          }

          function _download() {
            console.info(`Downloading ${dst_subdirectory}/${file0.name}`);
            download_file_from_share(`${src_subdirectory}/${file0.name}`, dirpath0 + '/' + file0.name, {
              size: file0.prv.size
            }, function(err) {
              if (err) {
                console.warn(`Problem downloading (err). Writing .prv instead.`)
                console.info('');
                _write_prv();
                return;
              }
              cb();
            });
          }

          function _write_prv() {
            console.info(`Writing ${dst_subdirectory}/${file0.name}.prv`)
            write_json_file(dirpath0 + '/' + file0.name + '.prv', file0.prv);
            cb();
          }
        }, function() {
          cb2();
        });
      }, function(cb2) {
        async.eachSeries(dirs, function(dir0, cb) {
          do_download_for_clone(opts, require('path').join(src_subdirectory, dir0.name), require('path').join(dst_subdirectory, dir0.name), function(err) {
            if (err) {
              callback(err);
              return;
            }
            cb();
          });
        }, function() {
          callback(null);
        });
      }]);
    });
  }

  function download_file_from_share(relpath_on_share, destpath, opts, callback) {
    var url = `${m_kbucket_url}/${m_config.kbNodeId()}/download/${encodeURIComponent(relpath_on_share)}`;
    download_file(url, destpath, opts, callback);
  }

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
          console.info(`Downloaded ${format_file_size(bytes_downloaded)} to ${dest_fname}.`);
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
        console.info(`Downloaded ${format_file_size(bytes_downloaded)} of ${format_file_size(bytes_total)} ...`);
      } else {
        console.info(`Downloaded ${format_file_size(bytes_downloaded)} ...`);
      }
    }

  }

  function readdir(subdirectory, callback) {
    var CC = new KBucketClient();
    CC.setKBucketUrl(m_kbucket_url);
    CC.readDir(m_config.kbNodeId(), subdirectory, function(err, files, dirs) {
      callback(err, files, dirs);
    });
  }

  function start_indexing(callback) {
    console.info('Starting indexing...');
    if (kbnode_type != 'share') {
      console.error('start_indexing is only for kbnode_type=share');
      process.exit(-1);
    }
    m_context.share_indexer.startIndexing(callback);
  }

  function start_websocket_server(callback) {
    if (kbnode_type != 'hub') {
      console.error('start_websocket_server is only for kbnode_type=hub');
      process.exit(-1);
    }
    //initialize the WebSocket server instance
    logger.info('Starting WebSocket server.');
    const wss = new WebSocket.Server({
      server: m_app.server
    });

    wss.on('connection', (ws, req) => {
      // Logging ////////////////////////////////
      const ip = req.connection.remoteAddress;
      var ip_forwarded_for;
      if (req.headers['x-forwarded-for']) {
        ip_forwarded_for = req.headers['x-forwarded-for'].split(/\s*,\s*/)[0];
      }
      logger.info('New websocket connection.', {
        ip: ip,
        ip_forwarded_for: ip_forwarded_for
      });
      ////////////////////////////////////////////

      on_new_websocket_connection(ws);
    });

    callback(null);
  }

  function on_new_websocket_connection(ws) {
    if (kbnode_type != 'hub') {
      console.error('on_new_websocket_connection is only for kbnode_type=hub');
      process.exit(-1);
    }

    var PWS = new PoliteWebSocket({
      wait_for_response: false,
      enforce_remote_wait_for_response: true,
      timeout_sec: 60
    });
    PWS.setSocket(ws);

    var CC = new KBConnectionToChildNode(m_config);
    CC.setWebSocket(PWS);
    CC.onRegistered(function() {
      logger.info('Child has registered', {
        info: CC.childNodeRegistrationInfo()
      });
      if (CC.childNodeType() == 'share') {

        // Everything looks okay, let's add this share to our share manager
        const logmsg = `Adding child share: ${CC.childNodeRegistrationInfo().name} (${CC.childNodeId()})`;
        logger.info(logmsg);
        console.info(logmsg);

        m_context.hub_manager.connectedShareManager().addConnectedShare(CC, function(err) {
          if (err) {
            PWS.sendErrorAndClose(`Error adding share: ${err}`);
            return;
          }
          // acknowledge receipt of the register message so that the child node can proceed
          CC.sendMessage({
            command: 'confirm_registration',
            info: m_config.getNodeInfo()
          });
        });
        //todo: how do we free up the CC object?
      } else if (CC.childNodeType() == 'hub') {
        // Everything looks okay, let's add this share to our share manager
        const logmsg = `Adding child hub: ${CC.childNodeRegistrationInfo().name} (${CC.childNodeId()})`;
        logger.info(logmsg);
        console.info(logmsg);

        m_context.hub_manager.connectedChildHubManager().addConnectedChildHub(CC, function(err) {
          if (err) {
            PWS.sendErrorAndClose(`Error adding child hub: ${err}`);
            return;
          }
          // acknowledge receipt of the register message so that the child node can proceed
          CC.sendMessage({
            command: 'confirm_registration',
            info: m_config.getNodeInfo()
          });
        });
      } else {
        PWS.sendErrorAndClose('Unexpected child node type: ' + CC.childNodeType());
      }
    });
  }

  function start_checking_config_exists(callback) {
    do_check();
    callback();

    function do_check() {
      if (!fs.existsSync(kbnode_directory + '/.kbucket/kbnode.json')) {
        console.info('Configuration file does not exist. Exiting.');
        process.exit(-1);
      }
      setTimeout(function() {
        do_check();
      }, 3000);
    }
  }

  function get_listen_port(callback) {
    if (kbnode_type == 'share') {
      // TODO: figure out better method for determining port in range
      get_free_port_in_range(KBUCKET_SHARE_PORT_RANGE.split('-'), function(err, listen_port) {
        if (err) {
          callback(err);
          return;
        }
        callback(null, listen_port);
      });
    } else {
      var port = m_config.getConfig('listen_port');
      callback(null, port);
    }
  }

  function get_free_port_in_range(range, callback) {
    if (range.length > 2) {
      callback('Invalid port range.');
      return;
    }
    if (range.length < 1) {
      callback('Invalid port range (*).');
      return;
    }
    if (range.length == 1) {
      range.push(range[0]);
    }
    range[0] = Number(range[0]);
    range[1] = Number(range[1]);
    findPort('127.0.0.1', range[0], range[1], function(ports) {
      if (ports.length == 0) {
        callback(`No free ports found in range ${range[0]}-${range[1]}`);
        return;
      }
      callback(null, ports[0]);
    });
  }

  function start_sending_node_data_to_parent(callback) {
    do_send_node_data_to_parent();
    callback();
  }

  function do_send_node_data_to_parent() {
    if (!m_context.connection_to_parent_hub) {
      finalize(1000);
      return;
    }
    const node_data = get_node_data_for_parent();

    let msg = {
      command: 'report_node_data'
    };
    if (m_last_node_data_reported) {
      let delta = jsondiffpatch.diff(m_last_node_data_reported, node_data);
      if (delta)
        msg.data_delta = delta;
      else
        msg.data_nochange = true;
    } else {
      msg.data = node_data;
    }
    m_last_node_data_reported = node_data;
    m_context.connection_to_parent_hub.sendMessage(msg);
    finalize(5000);

    function finalize(msec_timeout) {
      setTimeout(function() {
        do_send_node_data_to_parent();
      }, msec_timeout);
    }
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

/*
function write_text_file(fname, txt) {
  try {
    require('fs').writeFileSync(fname, txt);
    return true;
  } catch (err) {
    return false;
  }
}
*/

function write_json_file(fname, obj) {
  try {
    require('fs').writeFileSync(fname, JSON.stringify(obj, null, 4));
    return true;
  } catch (err) {
    return false;
  }
}