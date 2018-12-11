exports.find_file=find_file;

const async = require('async');

function find_file(context, opts, callback) {
  find_shares_with_file(context, opts, function(err, results) {
    if (err) {
      callback(err);
      return;
    }
    var node_data0 = context.hub_manager.nodeDataForParent();
    var urls = [];
    async.eachSeries(results, function(result, cb) {
      var kbshare_id = result.kbshare_id;
      var share0 = node_data0.descendant_nodes[kbshare_id];
      if (share0.listen_url) {
        const url0 = share0.listen_url + '/' + kbshare_id + '/download/' + result.path;
        urls.push(url0);
      }
      var visited = {}; //prevent infinite loop
      var hub_id = share0.parent_node_id;
      while (hub_id) {
        if (visited[hub_id])
          break;
        visited[hub_id] = true;
        if (hub_id in node_data0.descendant_nodes) {
          var hub0 = node_data0.descendant_nodes[hub_id];
          if (hub0.listen_url) {
            const url0 = hub0.listen_url + '/' + kbshare_id + '/download/' + result.path;
            urls.push(url0);
          }
          hub_id = hub0.parent_node_id;
        } else {
          hub_id = null;
        }
      }
      if (context.config.listenUrl()) {
        const url0 = context.config.listenUrl() + '/' + kbshare_id + '/download/' + result.path;
        urls.push(url0);
      }
      cb();
    }, function() {
      callback(null, {
        success: true,
        found: (results.length>0),
        urls: urls,
        results: results
      });
    });
  });
}

function find_shares_with_file(context, opts, callback) {
  find_child_shares_with_file(context, opts, function(err, results1) {
    if (err) {
      callback(err);
      return;
    }
    find_shares_with_file_in_child_hubs(context, opts, function(err, results2) {
      if (err) {
        callback(err);
        return;
      }
      var results = [];
      for (let i in results1) {
        results.push(results1[i]);
      }
      for (let i in results2) {
        results.push(results2[i]);
      }
      callback(null, results);
    });
  });
}

function find_shares_with_file_in_child_hubs(context, opts, callback) {
  // Find a file by checking all of the connected shares
  var kbnode_ids = context.hub_manager.connectedChildHubManager().connectedChildHubIds();

  var results = [];

  // Loop sequentially through each child hub id
  // TODO: shall we allow this to be parallel / asynchronous?
  async.eachSeries(kbnode_ids, function(kbnode_id, cb) {
    var SS = context.hub_manager.connectedChildHubManager().getConnectedChildHub(kbnode_id);
    if (!SS) { //maybe it disappeared
      cb(); // go to the next one
      return;
    }
    let urlpath0 = '';
    if (opts.kbshare_id) {
      urlpath0 = `${opts.kbshare_id}/find/${opts.sha1}/${opts.filename}`; 
    }
    else {
      urlpath0 = `find/${opts.sha1}/${opts.filename}`;  
    }
    SS.httpOverWebSocketClient().httpRequestJson(urlpath0, function(err, resp) {
      if (!err) {
        let results0 = resp.results || [];
        for (let i in results0) {
          results.push(results0[i]);
        }
      }
      cb();
    });
  }, function() {
    // we checked all the child hubs, now return the response.
    callback(null, results);
  });
}

function find_child_shares_with_file(context, opts, callback) {
  // Find a file by checking all of the connected shares
  var kbnode_ids = context.hub_manager.connectedLeafManager().connectedLeafIds();

  var results = [];

  // Loop sequentially through each share key
  // TODO: shall we allow this to be parallel / asynchronous?
  async.eachSeries(kbnode_ids, function(kbnode_id, cb) {
    if ((opts.kbshare_id) && (opts.kbshare_id != kbnode_id)) {
      cb(); // not the droid you are looking for
      return;
    }
    var SS = context.hub_manager.connectedLeafManager().getConnectedLeaf(kbnode_id);
    if (!SS) { //maybe it disappeared
      cb(); // go to the next one
      return;
    }
    // Find the file on this particular share

    let connection_to_child_node = SS.connectionToChildNode();
    var data0 = connection_to_child_node.childNodeData();
    var files_by_sha1 = data0.files_by_sha1 || {};
    if (opts.sha1 in files_by_sha1) {
      const kbnode_id = connection_to_child_node.childNodeId();
      results.push({
        kbshare_id: kbnode_id,
        size: files_by_sha1[opts.sha1].size,
        path: files_by_sha1[opts.sha1].path
      });
      cb();
    } else {
      cb();
    }
  }, function() {
    callback(null, results);
  });
}
