exports.KBHttpServer = KBHttpServer;

const express = require('express');
const cors = require('cors');

function KBHttpServer(API) {
  this.app = function() {
    return m_app;
  };

  let m_app = express();
  m_app.set('json spaces', 4); // when we respond with json, this is how it will be formatted
  m_app.use(cors());

  // API readdir
  m_app.get('/:kbshare_id/api/readdir/:subdirectory(*)', function(req, res) {
    var params = req.params;
    API.handle_readdir(params.kbshare_id, params.subdirectory, req, res);
  });
  m_app.get('/:kbshare_id/api/readdir/', function(req, res) {
    var params = req.params;
    API.handle_readdir(params.kbshare_id, '', req, res);
  });

  // API nodeinfo
  m_app.get('/:kbnode_id/api/nodeinfo', function(req, res) {
    var params = req.params;
    API.handle_nodeinfo(params.kbnode_id, req, res);
  });

  // API find in share
  m_app.get('/:kbshare_id/api/find/:sha1/:filename(*)', function(req, res) {
    var params = req.params;
    API.handle_find_in_share(params.kbshare_id, params.sha1, params.filename, req, res);
  });
  m_app.get('/:kbshare_id/api/find/:sha1/', function(req, res) {
    var params = req.params;
    API.handle_find_in_share(params.kbshare_id, params.sha1, '', req, res);
  });

  // API download
  m_app.get('/:kbshare_id/download/:filename(*)', function(req, res) {
    var params = req.params;
    API.handle_download(params.kbshare_id, params.filename, req, res);
  });

  // API download hdf5 data
  m_app.get('/:kbshare_id/hdf5/:filename(*)', function(req, res) {
    var params = req.params;
    API.handle_hdf5(params.kbshare_id, params.filename, req, res);
  });

  // API prv
  m_app.get('/:kbshare_id/prv/:filename(*)', function(req, res) {
    var params = req.params;
    API.handle_prv(params.kbshare_id, params.filename, req, res);
  });

  // API find (only for kbnode_type='hub')
  m_app.get('/find/:sha1/:filename(*)', function(req, res) {
    var params = req.params;
    API.handle_find(params.sha1, params.filename, req, res);
  });
  m_app.get('/find/:sha1/', function(req, res) {
    var params = req.params;
    API.handle_find(params.sha1, '', req, res);
  });
}

