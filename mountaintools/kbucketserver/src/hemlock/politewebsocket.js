exports.PoliteWebSocket = PoliteWebSocket;

const WebSocket = require('ws');
const logger = require(__dirname + '/logger.js').logger();

function PoliteWebSocket(opts) {
  opts = opts || {
    wait_for_response: false,
    enforce_remote_wait_for_response: false
  };

  // use one of the following two methods to initialize
  this.connectToRemote = function(url, callback) {
    connectToRemote(url, callback);
  };
  this.setSocket = function(ws) {
    m_ws = ws;
    setup();
  };

  // operations
  this.sendMessage = function(X) {
    sendMessage(X);
  };
  this.close = function() {
    close();
  };
  this.sendErrorAndClose = function(err) {
    send_error_and_close_socket(err);
  };
  /*
  this.forwardHttpRequest = function(req, res) {
    forward_http_request(req, res);
  };
  */

  // event handlers
  this.onMessage = function(handler) {
    m_on_message_handlers.push(handler);
  };
  this.onClose = function(handler) {
    m_on_close_handlers.push(handler);
  };
  this.onByteCount = function(handler) {
    m_on_byte_count_handlers.push(handler);
  };

  var m_received_response_since_last_message = true;
  var m_sent_message_since_last_response = true;
  var m_queued_messages = [];
  var m_ws = null;
  var m_on_message_handlers = [];
  var m_on_close_handlers = [];
  var m_on_byte_count_handlers = [];
  //var m_wait_to_send = true;
  let m_bytes_in_to_report = 0;
  let m_bytes_out_to_report = 0;
  let m_last_message_timestamp = new Date();

  function connectToRemote(url, callback) {
    m_ws = new WebSocket(url, {
      perMessageDeflate: false
    });
    m_ws.on('open', function() {
      logger.info('Connected to remote', {
        url: url
      });
      if (callback) {
        callback(null);
        callback = null;
      }
    });
    m_ws.on('error', function(err) {
      logger.error('Error connecting to remote', {
        url: url,
        err: err.message
      });
      if (callback) {
        callback('Websocket error: ' + err.message);
        callback = null;
        return;
      }
    });
    setup();
  }

  function call_on_close_handlers() {
    for (var i in m_on_close_handlers) {
      m_on_close_handlers[i]();
    }
  }

  function setup() {
    m_ws.on('close', function() {
      logger.info('Websocket closed.');
      call_on_close_handlers();
    });
    m_ws.on('error', function(err) {
      var msg = 'Websocket error: ' + err.message;
      logger.error(msg);
      console.error(msg);
      call_on_close_handlers();
    });
    m_ws.on('unexpected-response', function(err) {
      var msg = 'Websocket unexpected response: ' + err.message;
      logger.error(msg);
      console.error(msg);
    });
    m_ws.on('message', (message_str) => {
      report_bytes_in(message_str.length);
      m_last_message_timestamp = new Date();
      if ((opts.enforce_remote_wait_for_response) && (!m_sent_message_since_last_response)) {
        send_error_and_close_socket('Received message before sending response to last message.');
        return;
      }
      var msg = parse_json(message_str);
      if (!msg) {
        send_error_and_close_socket('Error parsing json of message');
        return;
      }
      m_received_response_since_last_message = true;
      m_sent_message_since_last_response = false;
      call_on_message_handlers(msg);
      check_send_queued_message();
    });
  }

  function call_on_message_handlers(msg) {
    for (var i in m_on_message_handlers) {
      m_on_message_handlers[i](msg);
    }
  }

  function send_error_and_close_socket(err) {
    var errstr = err + '. Closing websocket.';
    logger.error(errstr);
    console.error(errstr);
    if (m_ws.readyState == 1) {
      // open
      actually_send_message({
        error: errstr
      });
    }
    close();
  }

  function close() {
    m_ws.close();
  }

  function sendMessage(X) {
    X._timestamp = new Date();
    if ((opts.wait_for_response) && (!m_received_response_since_last_message)) {
      logger.info('Sending message', {
        command: X.command || ''
      });
      m_queued_messages.push(X);
    } else {
      actually_send_message(X);
    }
  }

  function actually_send_message(X) {
    if (m_ws.readyState != 1) {
      // the socket is not open
      return;
    }
    var elapsed = (new Date()) - X._timestamp;
    delete X._timestamp;
    var message_str = JSON.stringify(X);
    try {
      m_ws.send(message_str);
      report_bytes_out(message_str.length);
    } catch (err) {
      send_error_and_close_socket('Error sending websocket message: ' + err.message);
    }
    m_received_response_since_last_message = false;
    m_sent_message_since_last_response = true;
  }

  function check_send_queued_message() {
    if ((m_received_response_since_last_message) && (m_queued_messages.length > 0)) {
      var msg = m_queued_messages[0];
      m_queued_messages = m_queued_messages.slice(1);
      actually_send_message(msg);
    }
  }

  function report_bytes_in(num_bytes) {
    m_bytes_in_to_report += num_bytes;
    schedule_report_bytes();
  }

  function report_bytes_out(num_bytes) {
    m_bytes_out_to_report += num_bytes;
    schedule_report_bytes();
  }
  let m_report_bytes_scheduled = false;

  function schedule_report_bytes() {
    if (m_report_bytes_scheduled) return;
    m_report_bytes_scheduled = true;
    setTimeout(function() {
      m_report_bytes_scheduled = false;
      do_report_bytes();
    }, 1000);
  }

  function do_report_bytes() {
    if ((m_bytes_in_to_report) || (m_bytes_out_to_report)) {
      for (var i in m_on_byte_count_handlers) {
        m_on_byte_count_handlers[i](m_bytes_in_to_report, m_bytes_out_to_report);
      }
      m_bytes_in_to_report = 0;
      m_bytes_out_to_report = 0;
    }
  }

  function next_check_connection_timeout() {
    do_check_connection_timeout(function() {
      setTimeout(function() {
        next_check_connection_timeout();
      }, 5000);
    });
  }
  function do_check_connection_timeout(callback) {

    var elapsed_since_last_message_msec=(new Date())-m_last_message_timestamp;
    if (elapsed_since_last_message_msec>opts.timeout_sec*1000) {
      send_error_and_close_socket(`Closing connection after ${elapsed_since_last_message_msec/1000} seconds of not receiving a message.`);
      return; //don't call back so we end these checks
    }
    callback();
  }
  next_check_connection_timeout();
}

function parse_json(str) {
  try {
    return JSON.parse(str);
  } catch (err) {
    return null;
  }
}