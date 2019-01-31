exports.HemlockNode = HemlockNode;

const async = require('async');
const WebSocket = require('ws');
const findPort = require('find-port');
const fs = require('fs');
const axios = require('axios');
const jsondiffpatch = require('jsondiffpatch');
const object_hash = require('object-hash');
//const REQUEST = require('request');

const HemlockNodeConfig = require(__dirname + '/hemlocknodeconfig.js').HemlockNodeConfig;
const HemlockConnectionToChildNode = require(__dirname + '/hemlockconnectiontochildnode.js').HemlockConnectionToChildNode;
const HemlockConnectionToParentHub = require(__dirname + '/hemlockconnectiontoparenthub.js').HemlockConnectionToParentHub;
const HemlockHubManager = require(__dirname + '/hemlockhubmanager.js').HemlockHubManager;
const PoliteWebSocket = require(__dirname + '/politewebsocket.js').PoliteWebSocket;
const logger = require(__dirname + '/logger.js').logger();

// TODO: think of a better default range
const HEMLOCK_LEAF_PORT_RANGE = process.env.HEMLOCK_LEAF_PORT_RANGE || '2000-3000';
const HEMLOCK_LEAF_HOST = process.env.HEMLOCK_LEAF_HOST || 'localhost';

// hemlock node type: hub or leaf
function HemlockNode(hemlock_node_directory, node_type) {
  this.setHttpServer = function(app) {
    m_http_server = app;
  };
  this.initialize = function(opts, callback) {
    initialize(opts, callback);
  };
  this.setRootUrl = function(url) {
    m_root_url = url;
  };
  this.setLeafManager = function(MM) {
    m_context.leaf_manager = MM;
  };
  this.context = function() {
    return m_context;
  };


  let m_context = {};
  let m_last_node_data_reported = null;
  var m_http_server = null;
  m_context.connection_to_parent_hub = null;
  var m_root_url = process.env.KBUCKET_URL||'https://kbucket.flatironinstitute.org';
  let m_config_directory_name = '';
  let m_config_file_name = '';
  let m_config = null;

  // only used for node_type='hub'
  m_context.hub_manager = null;

  function initialize(opts, callback) {
    opts.config_directory_name = opts.config_directory_name || '.kbucket';
    opts.config_file_name = opts.config_file_name || 'kbnode.json';
    m_context.config = new HemlockNodeConfig(hemlock_node_directory, opts);
    m_config = m_context.config;
    m_config_directory_name = opts.config_directory_name;
    m_config_file_name = opts.config_file_name;

    if (node_type == 'hub')
      m_context.hub_manager = new HemlockHubManager(m_config);

    var steps = [];

    // for both types
    steps.push(create_config_if_needed);
    steps.push(generate_pem_keys_and_id_if_needed);
    steps.push(initialize_config);
    steps.push(run_interactive_config);
    if (!opts.no_server) {
      steps.push(start_http_server);
      if (node_type == 'hub') {
        steps.push(start_websocket_server);
      }
      steps.push(connect_to_parent_hub);
      steps.push(start_sending_node_data_to_parent);
      steps.push(start_checking_config_changed);
    }

    async.series(steps, function(err) {
      callback(err);
    });

    function run_interactive_config(callback) {
      m_config.runInteractiveConfiguration(opts, callback);
    }

    function create_config_if_needed(callback) {
      if (!m_config.configDirExists()) {
        console.info(`Creating ${node_type} configuration in ${m_config.hemlockNodeDirectory()}/${m_config_directory_name} ...`);
        m_config.createNew(node_type, opts, function(err) {
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
  }

  function initialize_config(callback) {
    console.info('Initializing configuration...');
    m_config.initialize(function(err) {
      if (err) {
        callback(err);
        return;
      }
      require(__dirname + '/logger.js').initialize({
        application: 'hemlock',
        directory: m_config.configDir() + '/logs'
      });
      if (m_config.hemlockNodeType() != node_type) {
        callback('Incorrect type for hemlock node: ' + m_config.hemlockNodeType());
        return;
      }
      callback(null);
    });
  }

  function start_http_server(callback) {
    if (!m_http_server) {
      callback('Http server not set.');
      return;
    }
    let app = m_http_server;

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
        node_type: node_type
      });
      app.server.listen(listen_port, function() {
        console.info(`${m_config.getConfig('network_type')} server is running ${app.protocol} on port ${app.port}`);
        callback(null);
      });
    });
  }

  function get_node_data_for_parent() {
    if (m_config.hemlockNodeType() == 'hub') {
      return m_context.hub_manager.nodeDataForParent();
    } else if (m_config.hemlockNodeType() == 'leaf') {
      if (!m_context.leaf_manager) {
        console.error('Leaf manager not set.');
        process.exit(-1);
      }
      return m_context.leaf_manager.nodeDataForParent();
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
      if (node_type == 'leaf') {
        callback('No parent hub url specified.');
      } else {
        callback(null);
      }
      return;
    }
    m_context.connection_to_parent_hub = new HemlockConnectionToParentHub(m_config);
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
      if (m_context.leaf_manager) {
        m_context.leaf_manager.restart();
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

  function start_websocket_server(callback) {
    if (node_type != 'hub') {
      console.error('start_websocket_server is only for node_type=hub');
      process.exit(-1);
    }
    //initialize the WebSocket server instance
    logger.info('Starting WebSocket server.');
    const wss = new WebSocket.Server({
      server: m_http_server.server
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
    if (node_type != 'hub') {
      console.error('on_new_websocket_connection is only for node_type=hub');
      process.exit(-1);
    }

    var PWS = new PoliteWebSocket({
      wait_for_response: false,
      enforce_remote_wait_for_response: true,
      timeout_sec: 60
    });
    PWS.setSocket(ws);

    var CC = new HemlockConnectionToChildNode(m_config);
    CC.setWebSocket(PWS);
    CC.onRegistered(function() {
      logger.info('Child has registered', {
        info: CC.childNodeRegistrationInfo()
      });
      if (CC.childNodeType() == 'leaf') {

        // Everything looks okay, let's add this leaf to our manager
        const logmsg = `Adding child (leaf): ${CC.childNodeRegistrationInfo().name} (${CC.childNodeId()})`;
        logger.info(logmsg);
        console.info(logmsg);

        m_context.hub_manager.connectedLeafManager().addConnectedLeaf(CC, function(err) {
          if (err) {
            PWS.sendErrorAndClose(`Error adding leaf: ${err}`);
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
        // Everything looks okay, let's add this hub to our manager
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

  function start_checking_config_changed(callback) {
    let config_file_mtime=null;

    do_check();
    callback();

    function do_check() {
      let config_fname=hemlock_node_directory + '/' + m_config_directory_name + '/' + m_config_file_name;
      if (!fs.existsSync(config_fname)) {
        console.info('Configuration file does not exist. Exiting.');
        process.exit(-1);
      }
      let stat0=stat_file(config_fname);
      if (!stat0) {
        console.info('Unable to stat config file. Exiting.');
        process.exit(-1);
      }
      if (config_file_mtime) {
        if ((stat0.mtime+'')!=(config_file_mtime+'')) {
            console.info('Configuration file has been modified. Exiting.');
            process.exit(-1);
        }
      }
      config_file_mtime=stat0.mtime;
      setTimeout(function() {
        do_check();
      }, 3000);
    }
  }

  function get_listen_port(callback) {
    if (node_type == 'leaf') {
      // TODO: figure out better method for determining port in range
      get_free_port_in_range(HEMLOCK_LEAF_PORT_RANGE.split('-'), function(err, listen_port) {
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
    setTimeout(function() {
      do_send_node_data_to_parent();
    }, 1000);
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
    msg.data_hash=object_hash(node_data);
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

function stat_file(fname) {
  try {
    return require('fs').statSync(fname);
  } catch (err) {
    return null;
  }
}