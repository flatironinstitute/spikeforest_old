const fs = require('fs');
const async = require('async');

const logger = require(__dirname + '/../hemlock/logger.js').logger();

exports.LariNodeApi = LariNodeApi;

const LariJobManager = require(__dirname + '/larijobmanager.js').LariJobManager;
const LariProcessorJob = require(__dirname + '/larijobmanager.js').LariProcessorJob;
const list_processors = require(__dirname + '/larijobmanager.js').list_processors;

const JobManager = new LariJobManager();

/*
Test from command-line:
curl --header "Content-Type: application/json"   --request POST   --data '{"processor_name":"ephys.bandpass_filter"}' http://localhost:2000/1592364262cc/api/run_process
*/

function LariNodeApi(context) {
  this.handle_nodeinfo = handle_nodeinfo;
  this.handle_run_process = handle_run_process;
  this.handle_probe_process = handle_probe_process;
  this.handle_cancel_process = handle_cancel_process;
  this.handle_processor_spec = handle_processor_spec;

  let m_context = context;

  this.handle_list_processors = handle_list_processors;

  function handle_list_processors(leaf_node_id, req, res) {
    console.log("Handle List Processors....");
    let obj = req.body || {};
    if (typeof(obj) != 'object') {
      send_500(res, 'Unexpected request body type.');
      return;
    }
    obj.opts = obj.opts || {};
    m_context.config.incrementMetric('num_requests_run_process');
    if (m_context.config.hemlockNodeId() != leaf_node_id) {
      route_http_request_to_node(leaf_node_id, `${leaf_node_id}/api/list_processors`, req, res);
      return;
    }
    if (m_context.config.hemlockNodeType() != 'leaf') {
      send_500(res, 'Cannot run process on node of type: ' + m_context.config.hemlockNodeType());
      return;
    }
    if (!check_passcode(obj)) {
      send_500(res, 'Incorrect passcode.');
      return;
    }

    list_processors(function cb(err,data) {
      if (!err) {
        let response = {
          success: true,
          error: err,
          info: data.split('\n').filter(x => x)
        }
        res.json(response);
      } else {
        console.err(err);
      }
    });
  }

  function handle_nodeinfo(node_id, req, res) {
    m_context.config.incrementMetric('num_requests_nodeinfo');
    if (m_context.config.hemlockNodeId() != node_id) {
      route_http_request_to_node(node_id, `${node_id}/api/nodeinfo`, req, res);
      return;
    }
    let resp_msg = {
      success: true
    };
    resp_msg.info = m_context.config.getNodeInfo();
    if (m_context.config.hemlockNodeType() == 'hub') {
      resp_msg.child_hubs = {};
      let CHM = m_context.hub_manager.connectedChildHubManager();
      let child_hub_ids = CHM.connectedChildHubIds();
      for (let ii in child_hub_ids) {
        let id = child_hub_ids[ii];
        let HH = CHM.getConnectedChildHub(id);
        resp_msg.child_hubs[id] = {
          name: HH.name(),
          listen_url: HH.listenUrl()
        };
      }

      resp_msg.child_leaf_nodes = {};
      let CSM = m_context.hub_manager.connectedLeafManager();
      let child_leaf_ids = CSM.connectedLeafIds();
      for (let ii in child_leaf_ids) {
        let id = child_leaf_ids[ii];
        let SS = CSM.getConnectedLeaf(id);
        resp_msg.child_leaf_nodes[id] = {
          name: SS.name(),
          listen_url: SS.listenUrl()
        };
      }
    }
    if (m_context.connection_to_parent_hub) {
      resp_msg.parent_hub_info = m_context.connection_to_parent_hub.parentHubInfo();
    }
    resp_msg.metrics = m_context.config.metrics();
    res.json(resp_msg);
  }

  function handle_run_process(leaf_node_id, req, res) {
    let obj = req.body || {};
    if (typeof(obj) != 'object') {
      send_500(res, 'Unexpected request body type.');
      return;
    }
    obj.opts = obj.opts || {};
    m_context.config.incrementMetric('num_requests_run_process');
    if (m_context.config.hemlockNodeId() != leaf_node_id) {
      route_http_request_to_node(leaf_node_id, `${leaf_node_id}/api/run_process`, req, res);
      return;
    }
    if (m_context.config.hemlockNodeType() != 'leaf') {
      send_500(res, 'Cannot run process on node of type: ' + m_context.config.hemlockNodeType());
      return;
    }

    if (!check_passcode(obj)) {
      send_500(res, 'Incorrect passcode.');
      return;
    }

    let JJ = new LariProcessorJob();
    JJ.setLariDirectory(m_context.config.hemlockNodeDirectory());
    if (!m_context.share_indexer) {
      console.error('share_indexer not set (in handle_run_process)');
      send_500(res, 'share_indexer not set.');
      return;
    }
    JJ.setShareIndexer(m_context.share_indexer);
    if (!m_context.kbucket_url) {
      console.error('kbucket url not set');
      process.exit(-1);
    }
    JJ.setKBucketUrl(m_context.kbucket_url);
    let processor_name = obj.processor_name;
    let inputs = obj.inputs || {};
    let outputs = obj.outputs || {};
    let parameters = obj.parameters || {};
    // important: do not pass through the opts here. select which ones are allowed to go through
    // for example processor_command_prefix would be a big security problem.
    let processor_opts = {};
    if (m_context.config.getConfig('processor_command_prefix'))
      processor_opts.processor_command_prefix = m_context.config.getConfig('processor_command_prefix');
    processor_opts.mode = obj.opts.mode || 'run';
    if (obj.opts.force_run)
      processor_opts.force_run = true;
    if (obj.opts.container)
      processor_opts.container = obj.opts.container;
    if (!processor_name) {
      res.json({
        success: false,
        error: 'processor_name is empty.'
      });
      return;
    }
    JJ.start(processor_name, inputs, outputs, parameters, processor_opts, function(err, resp) {
      if (err) {
        res.json({
          success: false,
          error: err
        });
        return;
      }
      JobManager.addJob(JJ);
      res.json({
        success: true,
        job_id: JJ.jobId()
      });
    });
  }

  function handle_probe_process(leaf_node_id, req, res) {
    let obj = req.body || {};
    if (typeof(obj) != 'object') {
      send_500(res, 'Unexpected request body type.');
      return;
    }
    m_context.config.incrementMetric('num_requests_probe_process');
    if (m_context.config.hemlockNodeId() != leaf_node_id) {
      route_http_request_to_node(leaf_node_id, `${leaf_node_id}/api/probe_process`, req, res);
      return;
    }
    if (m_context.config.hemlockNodeType() != 'leaf') {
      send_500(res, 'Cannot probe process on node of type: ' + m_context.config.hemlockNodeType());
      return;
    }

    if (!check_passcode(obj)) {
      send_500(res, 'Incorrect passcode.');
      return;
    }

    let job_id = obj.job_id;
    if (!job_id) {
      send_500(res, 'job_id is empty');
      return;
    }

    let JJ = JobManager.job(job_id);
    if (!JJ) {
      send_500(res, 'Unable to find job with id: ' + job_id);
      return;
    }

    let resp = {};
    resp.is_complete = JJ.isComplete();
    if (JJ.isComplete()) {
      resp.result = JJ.result();
    }
    resp.console_output = JJ.takeLatestConsoleOutput();
    JJ.keepAlive();
    res.json(resp);
  }

  function handle_cancel_process(leaf_node_id, req, res) {
    let obj = req.body || {};
    if (typeof(obj) != 'object') {
      send_500(res, 'Unexpected request body type.');
      return;
    }
    obj.opts = obj.opts || {};
    m_context.config.incrementMetric('num_requests_cancel_process');
    if (m_context.config.hemlockNodeId() != leaf_node_id) {
      route_http_request_to_node(leaf_node_id, `${leaf_node_id}/api/cancel_process`, req, res);
      return;
    }
    if (m_context.config.hemlockNodeType() != 'leaf') {
      send_500(res, 'Cannot cancel process on node of type: ' + m_context.config.hemlockNodeType());
      return;
    }

    if (!check_passcode(obj)) {
      send_500(res, 'Incorrect passcode.');
      return;
    }

    let job_id = obj.job_id;
    if (!job_id) {
      send_500(res, 'job_id is empty');
      return;
    }

    let JJ = JobManager.job(job_id);
    if (!JJ) {
      send_500(res, 'Unable to find job with id: ' + job_id);
      return;
    }

    JJ.cancel();
    res.json({
      info: 'canceled job.'
    });
  }

  function handle_processor_spec(leaf_node_id, req, res) {
    let obj = req.body || {};
    if (typeof(obj) != 'object') {
      send_500(res, 'Unexpected request body type.');
      return;
    }
    obj.opts = obj.opts || {};
    m_context.config.incrementMetric('num_requests_processor_spec');
    if (m_context.config.hemlockNodeId() != leaf_node_id) {
      route_http_request_to_node(leaf_node_id, `${leaf_node_id}/api/processor_spec`, req, res);
      return;
    }
    if (m_context.config.hemlockNodeType() != 'leaf') {
      send_500(res, 'Cannot processor_spec on node of type: ' + m_context.config.hemlockNodeType());
      return;
    }

    if (!check_passcode(obj)) {
      send_500(res, 'Incorrect passcode.');
      return;
    }

    let processor_name = obj.processor_name;
    if (!processor_name) {
      send_500(res, 'processor_name is empty');
      return;
    }

    JobManager.getProcessorSpec(processor_name, obj.opts, function(err, spec) {
      if (err) {
        send_500(res, 'Unable to get spec for processor ' + processor_name + ': ' + err);
        return;
      }
      res.json({
        spec: spec
      });
    });
  }

  function route_http_request_to_node(node_id, path, req, res) {
    logger.info('route_http_request_to_node', {
      node_id: node_id,
      path: path,
      req_headers: req.headers
    });
    if (m_context.config.hemlockNodeType() != 'hub') {
      send_500(res, 'Cannot route request from non-hub.');
      return;
    }
    m_context.hub_manager.routeHttpRequestToNode(node_id, path, req, res);
  }

  function check_passcode(obj) {
    let opts = obj.opts || {};
    return ((opts.lari_passcode || '') == (m_context.config.getConfig('processing_passcode') || ''));
  }
}

function send_404(res) {
  try {
    res.status(404).send('404: File Not Found');
  } catch (err2) {
    console.error('Problem sending 404 response: ' + err2.message);
  }
}

function send_500(res, err) {
  logger.error('send_500', {
    error: err
  });
  try {
    res.status(500).send({
      error: err
    });
  } catch (err2) {
    console.error('Problem sending 500 response: ' + err + ':' + err2.message);
  }
}

function parse_json_request(req) {
  try {
    return JSON.parse(req.body);
  } catch (err) {
    return null;
  }
}

function ends_with(str, str2) {
  return (str.slice(str.length - str2.length) == str2);
}

function parse_json(str) {
  try {
    return JSON.parse(str);
  } catch (err) {
    return null;
  }
}

function read_json_file(fname) {
  try {
    var txt = require('fs').readFileSync(fname, 'utf8')
    return parse_json(txt);
  } catch (err) {
    return null;
  }
}

function read_text_file(fname) {
  try {
    var txt = require('fs').readFileSync(fname, 'utf8')
    return txt;
  } catch (err) {
    return null;
  }
}
