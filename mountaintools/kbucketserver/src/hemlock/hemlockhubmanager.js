exports.HemlockHubManager = HemlockHubManager;

const async = require('async');
//const fs = require('fs');
//const request = require('request');
const logger = require(__dirname + '/logger.js').logger();

const HttpOverWebSocketClient = require(__dirname + '/httpoverwebsocket.js').HttpOverWebSocketClient;

var LIMITS = {
  max_connected_leaf_nodes: 1e3,
  max_connected_child_hubs: 10
};

function HemlockHubManager(config) {
  this.connectedLeafManager = function() {
    return m_connected_leaf_manager;
  };
  this.connectedChildHubManager = function() {
    return m_connected_child_hub_manager;
  };
  this.setTopHubUrl = function(url) {
    m_connected_child_hub_manager.setTopHubUrl(url);
  };
  this.nodeDataForParent = function() {
    return nodeDataForParent();
  };
  this.routeHttpRequestToNode = function(node_id, path, req, res) {
    routeHttpRequestToNode(node_id, path, req, res);
  };

  // The leaf manager (see HemlockConnectedLeafManager)
  var m_connected_leaf_manager = new HemlockConnectedLeafManager(config);
  // The connected child hub manager (see HemlockConnectedChildHubManager)
  var m_connected_child_hub_manager = new HemlockConnectedChildHubManager(config);

  function nodeDataForParent() {
    var data = {
      node_id: config.hemlockNodeId(),
      descendant_nodes: {}
    };
    var hemlock_leaf_ids = m_connected_leaf_manager.connectedLeafIds();
    for (let ii in hemlock_leaf_ids) {
      var hemlock_leaf_id = hemlock_leaf_ids[ii];
      var SS = m_connected_leaf_manager.getConnectedLeaf(hemlock_leaf_id);
      data.descendant_nodes[hemlock_leaf_id] = {
        node_id: hemlock_leaf_id,
        parent_node_id: config.hemlockNodeId(),
        listen_url: SS.listenUrl(),
        node_type: 'leaf'
      };
    }
    var hemlock_hub_ids = m_connected_child_hub_manager.connectedChildHubIds();
    for (let ii in hemlock_hub_ids) {
      var hemlock_hub_id = hemlock_hub_ids[ii];
      var HH = m_connected_child_hub_manager.getConnectedChildHub(hemlock_hub_id);
      data.descendant_nodes[hemlock_hub_id] = {
        node_id: hemlock_hub_id,
        parent_node_id: config.hemlockNodeId(),
        listen_url: HH.listenUrl(),
        node_type: 'hub'
      };
      var data0 = HH.childNodeData();
      data0.descendant_nodes = data0.descendant_nodes || {};
      for (let id in data0.descendant_nodes) {
        data.descendant_nodes[id] = data0.descendant_nodes[id];
      }
    }
    return data;
  }

  function routeHttpRequestToNode(node_id, path, req, res) {
    var SS = m_connected_leaf_manager.getConnectedLeaf(node_id);
    if (SS) {
      SS.processHttpRequest(path, req, res);
      return;
    }
    const HH0 = m_connected_child_hub_manager.getConnectedChildHub(node_id);
    if (HH0) {
      HH0.processHttpRequest(path, req, res);
      return;
    }
    var ids = m_connected_child_hub_manager.connectedChildHubIds();
    for (let ii in ids) {
      var id = ids[ii];
      const HH_child = m_connected_child_hub_manager.getConnectedChildHub(id);
      var data0 = HH_child.childNodeData();
      var dn0 = data0.descendant_nodes || {};
      if (node_id in dn0) {
        HH_child.processHttpRequest(path, req, res);
        return;
      }
    }
    res.status(500).send({
      error: 'Unable to locate node with id: ' + node_id
    });
  }
}

function HemlockConnectedLeafManager(config) {
  // Manage a collection of HemlockConnectedLeaf objects, each representing a connected leaf
  this.addConnectedLeaf = function(connection_to_child_node, callback) {
    addConnectedLeaf(connection_to_child_node, callback);
  };
  this.connectedLeafIds = function() {
    return Object.keys(m_connected_leaf_nodes);
  };
  this.getConnectedLeaf = function(node_id) {
    return m_connected_leaf_nodes[node_id] || null;
  };

  var m_connected_leaf_nodes = {};

  function addConnectedLeaf(connection_to_child_node, callback) {
    // Add a new connected leaf

    var num_connected_leaf_nodes = Object.keys(m_connected_leaf_nodes).length;
    if (num_connected_leaf_nodes >= LIMITS.max_connected_leaf_nodes) {
      callback('Exceeded maximum number of child leaf connections.');
      return;
    }

    var node_id = connection_to_child_node.childNodeId();

    if (node_id in m_connected_leaf_nodes) {
      callback(`A connected leaf with id=${node_id} already exists.`);
      return;
    }

    connection_to_child_node.onClose(function() {
      remove_connected_leaf(node_id);
    });

    // create a new HemlockConnectedLeaf object, and pass in the connection object
    m_connected_leaf_nodes[node_id] = new HemlockConnectedLeaf(connection_to_child_node, config);
    callback(null);
  }

  function remove_connected_leaf(node_id) {
    // remove the leaf from the manager
    if (!(node_id in m_connected_leaf_nodes)) {
      // we don't have it anyway
      return;
    }
    // actually remove it
    var logmsg = `Removing child leaf: ${node_id}`;
    logger.info(logmsg);
    console.info(logmsg);
    delete m_connected_leaf_nodes[node_id];
  }
}

function HemlockConnectedLeaf(connection_to_child_node, config) {
  // Encapsulate a single leaf (child node)
  this.processHttpRequest = function(path, req, res) {
    processHttpRequest(path, req, res);
  };
  this.name = function() {
    var data = connection_to_child_node.childNodeRegistrationInfo();
    return data.name;
  };
  this.listenUrl = function() {
    var data = connection_to_child_node.childNodeRegistrationInfo();
    return data.listen_url;
  };
  this.connectionToChildNode=function() {
    return connection_to_child_node;
  }
  this.childNodeData = function() {
    return connection_to_child_node.childNodeData();
  };

  connection_to_child_node.onMessage(function(msg) {
    process_message_from_connected_leaf(msg, function(err, response) {
      if (err) {
        connection_to_child_node.reportErrorAndCloseSocket(err);
        return;
      }
      if (!response) {
        response = {
          message: 'ok'
        };
      }
      connection_to_child_node.sendMessage(response);
    });
  });

  // todo: move this http client to the connection_to_child_node and handle all http stuff there
  var m_http_over_websocket_client = new HttpOverWebSocketClient(send_message_to_leaf);
  m_http_over_websocket_client.onByteCount(function(num_bytes_in, num_bytes_out) {
    config.incrementMetric('http_bytes_in_from_child_leaf', num_bytes_in);
    config.incrementMetric('http_bytes_out_to_child_leaf', num_bytes_out);
  });

  function send_message_to_leaf(msg) {
    connection_to_child_node.sendMessage(msg);
  }

  ////////////////////////////////////////////////////////////////////////

  function process_message_from_connected_leaf(msg, callback) {
    // We got a message msg from the leaf computer

    // todo: move this http client to the connection_to_child_node and handle all http stuff there
    if (msg.message_type == 'http') {
      m_http_over_websocket_client.processMessageFromServer(msg, function(err) {
        if (err) {
          callback('Error in http over websocket: ' + err);
          return;
        }
        callback(null);
      });
      return;
    }

    {
      // Unrecognized command
      callback(`Unrecognized command: ${msg.command}`);
    }
  }

  function processHttpRequest(path, req, res) {
    // Forward a http request through the websocket to the leaf computer

    m_http_over_websocket_client.handleRequest(path, req, res);
  }
}

function HemlockConnectedChildHubManager(config) {
  // Manage a collection of HemlockConnectedChildHub objects, each representing a connected child hub
  this.addConnectedChildHub = function(connection_to_child_node, callback) {
    addConnectedChildHub(connection_to_child_node, callback);
  };
  this.connectedChildHubIds = function() {
    return Object.keys(m_connected_child_hubs);
  };
  this.getConnectedChildHub = function(node_id) {
    return m_connected_child_hubs[node_id] || null;
  };

  var m_connected_child_hubs = {};

  config.onTopHubUrlChanged(function() {
    send_message_to_all_child_hubs({
      command: 'set_top_hub_url',
      top_hub_url: config.topHubUrl()
    });
  });

  function send_message_to_all_child_hubs(msg) {
    for (let id in m_connected_child_hubs) {
      m_connected_child_hubs[id].sendMessage(msg);
    }
  }

  function addConnectedChildHub(connection_to_child_node, callback) {
    // Add a new connected leaf

    var num_connected_child_hubs = Object.keys(m_connected_child_hubs).length;
    if (num_connected_child_hubs >= LIMITS.max_connected_child_hubs) {
      callback('Exceeded maximum number of child hub connections.');
      return;
    }

    var node_id = connection_to_child_node.childNodeId();

    if (node_id in m_connected_child_hubs) {
      callback(`A child hub with id=${node_id} already exists.`);
      return;
    }

    connection_to_child_node.onClose(function() {
      remove_connected_child_hub(node_id);
    });

    // create a new HemlockConnectedChildHub object, and pass in the connection object
    m_connected_child_hubs[node_id] = new HemlockConnectedChildHub(connection_to_child_node, config);

    m_connected_child_hubs[node_id].sendMessage({
      command: 'set_top_hub_url',
      top_hub_url: config.topHubUrl()
    });

    callback(null);
  }

  function remove_connected_child_hub(node_id) {
    // remove the leaf from the manager
    if (!(node_id in m_connected_child_hubs)) {
      // we don't have it anyway
      return;
    }
    // actually remove it
    var logmsg = `Removing child hub: ${node_id}`;
    logger.info(logmsg);
    console.info(logmsg);
    delete m_connected_child_hubs[node_id];
  }
}

function HemlockConnectedChildHub(connection_to_child_node, config) {
  // Encapsulate a single child hub
  this.processHttpRequest = function(path, req, res) {
    processHttpRequest(path, req, res);
  };
  this.sendMessage = function(msg) {
    connection_to_child_node.sendMessage(msg);
  };
  this.childNodeData = function() {
    return connection_to_child_node.childNodeData();
  };
  this.name = function() {
    var data = connection_to_child_node.childNodeRegistrationInfo();
    return data.name;
  };
  this.listenUrl = function() {
    var data = connection_to_child_node.childNodeRegistrationInfo();
    return data.listen_url;
  };
  this.httpOverWebSocketClient=function() {
    return m_http_over_websocket_client;
  };

  connection_to_child_node.onMessage(function(msg) {
    process_message_from_connected_child_hub(msg, function(err, response) {
      if (err) {
        connection_to_child_node.reportErrorAndCloseSocket(err);
        return;
      }
      if (!response) {
        response = {
          message: 'ok'
        };
      }
      connection_to_child_node.sendMessage(response);
    });
  });

  //var m_response_handlers = {}; // handlers corresponding to requests we have sent to the child hub

  // todo: move this http client to the connection_to_child_node and handle all http stuff there
  var m_http_over_websocket_client = new HttpOverWebSocketClient(send_message_to_child_hub);
  m_http_over_websocket_client.onByteCount(function(num_bytes_in, num_bytes_out) {
    config.incrementMetric('http_bytes_in_from_child_hub', num_bytes_in);
    config.incrementMetric('http_bytes_out_to_child_hub', num_bytes_out);
  });

  function send_message_to_child_hub(msg) {
    connection_to_child_node.sendMessage(msg);
  }

  ////////////////////////////////////////////////////////////////////////

  function process_message_from_connected_child_hub(msg, callback) {
    // We got a message msg from the leaf computer

    // todo: move this http client to the connection_to_child_node and handle all http stuff there
    if (msg.message_type == 'http') {
      m_http_over_websocket_client.processMessageFromServer(msg, function(err) {
        if (err) {
          callback('Error in http over websocket: ' + err);
          return;
        }
        callback(null);
      });
      return;
    }
  }

  function processHttpRequest(path, req, res) {
    // Forward a http request through the websocket to the leaf computer

    m_http_over_websocket_client.handleRequest(path, req, res);
  }
}

function is_valid_sha1(sha1) {
  // check if this is a valid SHA-1 hash
  if (sha1.match(/\b([a-f0-9]{40})\b/))
    return true;
  return false;
}

