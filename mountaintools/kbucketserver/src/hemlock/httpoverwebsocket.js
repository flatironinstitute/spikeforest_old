exports.HttpOverWebSocketClient = HttpOverWebSocketClient;
exports.HttpOverWebSocketServer = HttpOverWebSocketServer;

const request = require('request');
const EventEmitter = require('events');
class MyEmitter extends EventEmitter {}

function HttpOverWebSocketServer(message_sender) {
  this.processMessageFromClient = function(msg, callback) {
    return processMessageFromClient(msg, callback);
  };
  this.setForwardUrl = function(url) {
    m_forward_url = url;
  };
  this.onByteCount = function(handler) {
    m_on_byte_count_handlers.push(handler);
  };

  var HTTP_REQUESTS = {};
  var m_forward_url = '';
  var m_on_byte_count_handlers = [];
  var m_bytes_in_to_report = 0;
  var m_bytes_out_to_report = 0;

  function processMessageFromClient(msg, callback) {
    process_http_message(msg, callback);
  }

  function process_http_message(msg, callback) {
    if (msg.command == 'http.initiate_request') {
      if (msg.request_id in HTTP_REQUESTS) {
        callback(`Request with id=${msg.request_id} already exists (in http.initiate_request).`);
        return;
      }
      HTTP_REQUESTS[msg.request_id] = new HttpRequest(m_forward_url, function(response_message) {
        response_message.request_id = msg.request_id;
        response_message.message_type = 'http';
        message_sender(response_message);
      });
      HTTP_REQUESTS[msg.request_id].initiateRequest(msg);
    } else if (msg.command == 'http.write_request_data') {
      if (!(msg.request_id in HTTP_REQUESTS)) {
        console.error(`No request found with id=${msg.request_id} (in http.write_request_data).`);
        return;
      }
      let REQ = HTTP_REQUESTS[msg.request_id];
      var data = Buffer.from(msg.data_base64, 'base64');
      REQ.writeRequestData(data);
    } else if (msg.command == 'http.end_request') {
      if (!(msg.request_id in HTTP_REQUESTS)) {
        callback(`No request found with id=${msg.request_id} (in http.end_request).`);
        return;
      }
      let REQ = HTTP_REQUESTS[msg.request_id];
      REQ.endRequest();
    } else if (msg.message == 'ok') {
      // just ok.
    } else {
      callback(`Unexpected http command: ${msg.command}.`);
      return;
    }
    callback(null);
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
}

function HttpOverWebSocketClient(message_sender) {
  this.processMessageFromServer = function(msg, callback) {
    return processMessageFromServer(msg, callback);
  };
  this.handleRequest = function(path, req, res) {
    handleRequest(path, req, res);
  };
  this.httpRequestJson = function(path, callback) {
    httpRequestJson(path, callback);
  };
  this.onByteCount = function(handler) {
    m_on_byte_count_handlers.push(handler);
  };

  var m_response_handlers = {};
  var m_on_byte_count_handlers = [];
  var m_bytes_in_to_report = 0;
  var m_bytes_out_to_report = 0;

  function processMessageFromServer(msg, callback) {
    process_http_message_from_server(msg, callback);
  }

  function process_http_message_from_server(msg, callback) {
    if (!(msg.request_id in m_response_handlers)) {
      callback(`Problem: Request id not found (in ${msg.command}): ${msg.request_id}`);
      return;
    }
    if (msg.command == 'http.set_response_headers') {
      // Set the headers for the response to the forwarded http request
      m_response_handlers[msg.request_id].setResponseHeaders(msg.status, msg.status_message, msg.headers);
    } else if (msg.command == 'http.write_response_data') {
      // Write response data for forwarded http request
      var data = Buffer.from(msg.data_base64, 'base64');
      m_response_handlers[msg.request_id].writeResponseData(data);
    } else if (msg.command == 'http.end_response') {
      // End response for forwarded http request
      m_response_handlers[msg.request_id].endResponse();
    } else if (msg.command == 'http.report_error') {
      // Report response error for forwarded http request (other than those reported in setResponseHeaders above)
      m_response_handlers[msg.request_id].reportError(msg.error);
    } else {
      callback('Unexpected http command: ' + msg.command);
    }
    callback(null);
  }

  function httpRequestJson(path, callback) {
    var req = new MyEmitter();
    var res = new MyEmitter();
    req.method = 'GET';
    req.headers = {};
    res.status = function(status_code, status_message) {
      if (status_code != 200) {
        respond('Error (status=' + status_code + '): ' + status_message);
        return;
      }
    };
    res.set = function() {
      //dummy
    };
    var response_body = '';
    res.write = function(txt) {
      response_body += (txt + '');
    };
    res.end = function() {
      try {
        var obj = JSON.parse(response_body);
        respond(null, obj);
      } catch (err) {
        respond('Error parsing json response.');
        return;
      }
    };

    handleRequest(path, req, res);
    req.emit('end');

    function respond(err, obj) {
      if (callback) {
        var callback2 = callback;
        callback = null;
        callback2(err, obj);
        return;
      }
    }
  }

  function handleRequest(path, req, res) {
    // make a unique id for the request (will be included in all correspondence)
    var req_id = make_random_id(8);

    // Various handler functions (callbacks) associated with the request
    m_response_handlers[req_id] = {
      setResponseHeaders: set_response_headers,
      writeResponseData: write_response_data,
      endResponse: end_response,
      reportError: report_error
    };

    // Initiate the request
    message_sender({
      message_type: 'http',
      command: 'http.initiate_request',
      method: req.method, // http request method
      path: path, // path of the url in the request
      query: req.query,
      headers: req.headers, // request headers
      request_id: req_id, // the unique id used in all correspondence
      body: req.body||undefined
    });

    var sent = false;

    req.on('data', function(data) {
      // We received some data from the client, so we'll pass it on to the server
      // TODO: do not base64 encode, and do not json encode -- handle this differently
      message_sender({
        message_type: 'http',
        command: 'http.write_request_data',
        data_base64: data.toString('base64'),
        request_id: req_id
      });
      report_bytes_in(data.length);
    });

    req.on('end', function() {
      // Request from the client has ended. pass on this info to the server
      message_sender({
        message_type: 'http',
        command: 'http.end_request',
        request_id: req_id
      });
    });

    function set_response_headers(status, status_message, headers) {
      // Set the response headers and status info -- this is info coming from the server
      if (sent) return;
      res.status(status, status_message);
      if ((headers.location) && (headers.location.startsWith('/'))) {
        // Redirects are tricky when we are manipulating the path
        // Need to handle this as a special case
        // TODO: handle this better... rather than hard-coding... on the other hand, this only affects serving web pages
        headers.location = '/share' + headers.location;
      }
      for (var hkey in headers) {
        // Set each header individually
        res.set(hkey, headers[hkey]);
      }
    }

    function write_response_data(data) {
      if (sent) return;
      // Write response data (this data comes from the server)
      res.write(data);
      report_bytes_out(data.length);
    }

    function end_response() {
      // End the response -- we are done writing -- this was triggered by a message from the server
      res.end();
      sent = true;
    }

    function report_error(err) {
      // Report an error for the response -- this was triggered by a message from the server
      var errstr = 'Error in response: ' + err;
      console.error(errstr);
      res.status(500).send({
        error: errstr
      });
      sent = true;
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
}

function HttpRequest(forward_url, on_message_handler) {
  this.initiateRequest = function(msg) {
    initiateRequest(msg);
  };
  this.writeRequestData = function(data) {
    writeRequestData(data);
  };
  this.endRequest = function() {
    endRequest();
  };

  var m_request = null;

  function initiateRequest(msg) {
    /*
    var opts={
      method:msg.method,
      hostname:'localhost',
      port:KBUCKET_SHARE_PORT,
      path:msg.path,
      headers:msg.headers
    };
    */
    var opts = {
      method: msg.method,
      uri: `${forward_url}/${msg.path}`,
      headers: msg.headers,
      query: msg.query,
      followRedirect: false // important because we want the proxy server to handle it instead
    };
    opts.headers.host = undefined; //This is important because I was having trouble with the SSL certificates getting confused
    m_request = request(opts);
    m_request.on('response', function(resp) {
      on_message_handler({
        command: 'http.set_response_headers',
        status: resp.statusCode,
        status_message: resp.statusMessage,
        headers: resp.headers
      });
      resp.on('error', on_response_error);
      resp.on('data', on_response_data);
      resp.on('end', on_response_end);
    });
    m_request.on('error', function(err) {
      on_message_handler({
        command: 'http.report_error',
        error: 'Error in request: ' + err.message
      });
    });
    if (msg.body) {
      let body=msg.body;
      if (typeof(body)=='object') {
        body=JSON.stringify(body);
      }
      m_request.write(body);
    }
  }

  function writeRequestData(data) {
    if (!m_request) {
      console.error('Unexpected: m_request is null in writeRequestData.');
      return;
    }
    m_request.write(data);
    report_bytes_out(data.length);
  }

  function endRequest() {
    if (!m_request) {
      console.error('Unexpected: m_request is null in endRequest.');
      return;
    }
    m_request.end();
  }

  function on_response_data(data) {
    on_message_handler({
      command: 'http.write_response_data',
      data_base64: data.toString('base64')
    });
  }

  function on_response_end() {
    on_message_handler({
      command: 'http.end_response'
    });
  }

  function on_response_error(err) {
    on_message_handler({
      command: 'http.report_error',
      error: 'Error in response: ' + err.message
    });
  }
}

function make_random_id(len) {
  // return a random string of characters
  var text = "";
  var possible = "ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz0123456789";

  for (var i = 0; i < len; i++)
    text += possible.charAt(Math.floor(Math.random() * possible.length));

  return text;
}