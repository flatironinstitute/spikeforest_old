exports.LariHttpServer = LariHttpServer;

const express = require('express');
const cors = require('cors');

function LariHttpServer(API) {
  this.app = function() {
    return m_app;
  };

  let m_app = express();
  m_app.set('json spaces', 4); // when we respond with json, this is how it will be formatted
  m_app.use(cors());

  m_app.use(express.json());

  // API nodeinfo
  m_app.get('/:node_id/api/nodeinfo', function(req, res) {
    var params = req.params;
    API.handle_nodeinfo(params.node_id, req, res);
  });
  m_app.post('/:leaf_node_id/api/list_processors', function(req, res) {
    var params = req.params;
    API.handle_list_processors(params.leaf_node_id, req, res);
  });

  // API nodeinfo
  m_app.post('/:leaf_node_id/api/run_process', function(req, res) {
    var params = req.params;
    API.handle_run_process(params.leaf_node_id, req, res);
  });
  m_app.post('/:leaf_node_id/api/probe_process', function(req, res) {
    var params = req.params;
    API.handle_probe_process(params.leaf_node_id, req, res);
  });
  m_app.post('/:leaf_node_id/api/cancel_process', function(req, res) {
    var params = req.params;
    API.handle_cancel_process(params.leaf_node_id, req, res);
  });
  m_app.post('/:leaf_node_id/api/processor_spec', function(req, res) {
    var params = req.params;
    API.handle_processor_spec(params.leaf_node_id, req, res);
  });
}

