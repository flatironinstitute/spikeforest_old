exports.KBConnectionToParentHub = KBConnectionToParentHub;

const crypto = require('crypto');
const logger = require(__dirname + '/logger.js').logger();

const PoliteWebSocket = require(__dirname + '/politewebsocket.js').PoliteWebSocket;
const HttpOverWebSocketServer = require(__dirname + '/httpoverwebsocket.js').HttpOverWebSocketServer;

function KBConnectionToParentHub(config) {
  this.initialize = function(parent_hub_url, callback) {
    initialize(parent_hub_url, callback);
  };
  this.sendMessage = function(msg) {
    sendMessage(msg);
  };
  this.onClose = function(handler) {
    m_on_close_handlers.push(handler);
  };
  this.parentHubInfo = function() {
    return m_parent_hub_info;
  };

  var m_parent_hub_socket = null;
  var m_http_over_websocket_server = null;
  var m_on_close_handlers = [];
  var m_parent_hub_info = null;
  var m_parent_hub_url = '';

  function initialize(parent_hub_url, callback) {
    m_parent_hub_url = parent_hub_url;
    var parent_hub_ws_url = get_websocket_url_from_http_url(parent_hub_url);
    m_parent_hub_socket = new PoliteWebSocket({
      wait_for_response: true,
      enforce_remote_wait_for_response: false
    });
    m_parent_hub_socket.onByteCount(function(num_bytes_in,num_bytes_out) {
      config.incrementMetric('bytes_in_from_parent_hub',num_bytes_in);
      config.incrementMetric('bytes_out_to_parent_hub',num_bytes_out);
    });
    m_http_over_websocket_server = new HttpOverWebSocketServer(sendMessage);
    m_http_over_websocket_server.onByteCount(function(bytes_in,bytes_out) {
      config.incrementMetric('http_bytes_in_from_parent_hub',num_bytes_in);
      config.incrementMetric('http_bytes_out_to_parent_hub',num_bytes_out);
    });
    m_http_over_websocket_server.setForwardUrl(config.listenUrl());
    m_parent_hub_socket.connectToRemote(parent_hub_ws_url, function(err) {
      if (err) {
        config.incrementMetric('parent_hub_connections_failed');
        callback(err);
        return;
      }
      register_with_parent_hub(function(err) {
        if (err) {
          config.incrementMetric('parent_hub_registrations_failed');
          callback(err);
          return;
        }
        config.incrementMetric('parent_hub_connections');
        m_parent_hub_socket.onClose(function() {
          config.incrementMetric('parent_hub_connections_closed');
          console.info(`Websocket closed.`);
          for (var i in m_on_close_handlers) {
            m_on_close_handlers[i]();
          }
        });
        callback(null);
      });
    });
    m_parent_hub_socket.onMessage(function(msg) {
      config.incrementMetric('messages_from_parent_hub');
      process_message_from_parent_hub(msg);
    });
  }

  function register_with_parent_hub(callback) {
    var listen_url = config.listenUrl();
    var command = 'register_child_node';
    var info = {
      listen_url: `${listen_url}`,
      name: config.getConfig('name'),
      kbnode_type: config.kbNodeType(),
      scientific_research: config.getConfig('scientific_research'),
      description: config.getConfig('description'),
      owner: config.getConfig('owner'),
      owner_email: config.getConfig('owner_email')
    };
    if (config.kbNodeType() == 'share') {
      info.confirm_share = config.getConfig('confirm_share');
    }
    sendMessage({
      command: command,
      info: info
    });
    callback();
  }

  function process_message_from_parent_hub(msg) {
    /*
    console.log('==============================================================');
    console.log('==============================================================');
    console.log(msg);
    console.log('==============================================================');
    console.log('==============================================================');
    console.log('');
    console.log('');
    */

    if (msg.error) {
      console.error(`Error from hub: ${msg.error}`);
      return;
    }

    if (msg.message_type == 'http') {
      if (m_http_over_websocket_server) {
        config.incrementMetric('http_messages_from_parent_hub');
        m_http_over_websocket_server.processMessageFromClient(msg, function(err) {
          if (err) {
            console.error('http over websocket error: ' + err + '. Closing websocket.');
            m_parent_hub_socket.close();
          }
        });
      } else {
        console.error('no http over websocket server set. Closing websocket.');
        m_parent_hub_socket.close();
      }
      return;
    }
    if (msg.command == 'set_top_hub_url') {
      config.setTopHubUrl(msg.top_hub_url);
    } else if (msg.command == 'confirm_registration') {
      console.info(`Connected to parent hub: ${msg.info.name}`);
      if (m_parent_hub_url) {
        var web_interface_url = `https://kbucketgui.herokuapp.com/?${config.kbNodeType()}=${config.kbNodeId()}`;
        console.info(`Web interface: ${web_interface_url}`);
      }
      m_parent_hub_info = msg.info;
    } else if (msg.message == 'ok') {
      // just ok.
    } else {
      console.info(`Unexpected command: ${msg.command}. Closing websocket.`);
      m_parent_hub_socket.close();
      return;
    }
  }

  function sendMessage(msg) {
    msg.timestamp = (new Date()) - 0;
    msg.kbnode_id = config.kbNodeId();
    var signature = sign_message(msg, config.privateKey());
    var X = {
      message: msg,
      kbnode_id: config.kbNodeId(),
      signature: signature
    };
    if (msg.command.startsWith('register')) {
      // send the public key on the first message
      X.public_key = config.publicKey();
    }

    m_parent_hub_socket.sendMessage(X);
  }

  function sign_message(msg, private_key) {
    const signer = crypto.createSign('sha256');
    signer.update(JSON.stringify(msg));
    signer.end();

    const signature = signer.sign(private_key);
    const signature_hex = signature.toString('hex');

    return signature_hex;
  }
}

function get_websocket_url_from_http_url(url) {
  var URL = require('url').URL;
  var url_ws = new URL(url);
  if (url_ws.protocol == 'http:')
    url_ws.protocol = 'ws';
  else
    url_ws.protocol = 'wss';
  url_ws = url_ws.toString();
  return url_ws;
}