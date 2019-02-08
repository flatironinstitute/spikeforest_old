const KBShareBrowser = require(__dirname + '/kbsharebrowser.js').KBShareBrowser;
const KBHubBrowser = require(__dirname + '/kbhubbrowser.js').KBHubBrowser;
const LariJobWidget = require(__dirname + '/larijobwidget.js').LariJobWidget;

var TOP_KBUCKET_HUB_URL = 'https://kbucket.flatironinstitute.org';
var DEFAULT_HUB_ID = 'a31ff6b646de';

$(document).ready(function() {
  var query = parse_url_params();
  window.query = query;

  if (query.lari_job_id) {
    if (query.lari_job_id=='test') query.lari_job_id='69r69uijzO_test';
    if (query.lari_id=='test') query.lari_id='133898b2b079';

    view_lari_job(query);
    return;
  }

  var kbnode_id = query.share || query.hub || query.node_id;
  if (!kbnode_id) {
    query.hub = DEFAULT_HUB_ID;
    kbnode_id = query.hub;
  }
  if (!kbnode_id) {
    $('#main_window').append('Missing query parameter: share, hub, or node_id');
    return;
  }

  if (query.kbucket_url) {
    TOP_KBUCKET_HUB_URL = query.kbucket_url;
  }

  get_node_info(kbnode_id, function(err, resp) {
    if (err) {
      $('#main_window').append(err);
      return;
    }
    let node_info=resp.info;
    let node_type=node_info.node_type;
    find_lowest_accessible_hub_url(kbnode_id, function(err, hub_url) {
      if (err) {
        $('#main_window').append(err);
        return;
      }
      if ((node_type=='leaf')||(node_type=='share')) {
        let W = new KBShareBrowser();
        W.setKBHubUrl(hub_url);
        $('#main_window').append(W.element());
        W.setKBShareId(kbnode_id);
      } else if (node_type=='hub') {
        let W = new KBHubBrowser();
        W.setKBHubUrl(hub_url);
        $('#main_window').append(W.element());
        W.setKBHubId(kbnode_id);
      }
    });
  });
});

function view_lari_job(query) {
  console.log(query);
  let W=new LariJobWidget();
  W.setLariId(query.lari_id||'');
  W.setLariJobId(query.lari_job_id||'');
  $('#main_window').append(W.element());
}

function find_lowest_accessible_hub_url(kbnode_id, callback) {
  get_node_info(kbnode_id, function(err, resp, accessible) {
    if (err) {
      callback(err);
      return;
    }
    let info = resp.info || {};
    let parent_hub_info = resp.parent_hub_info || {};
    if ((accessible) && (info.node_type == 'hub')) {
      callback(null, info.listen_url);
      return;
    }
    if (!parent_hub_info) {
      callback('Unable to find accessible hub.');
      return;
    }
    find_lowest_accessible_hub_url(parent_hub_info.kbnode_id||parent_hub_info.node_id, callback);
  });
}

function get_node_info(kbnode_id, callback) {
  var url = `${TOP_KBUCKET_HUB_URL}/${kbnode_id}/api/nodeinfo`;
  get_json(url, function(err, resp) {
    if (err) {
      callback('Error getting node info: ' + err);
      return;
    }
    if (!resp.info) {
      callback('Unexpected: response missing info field.');
      return;
    }
    //check accessible
    var check_url = `${resp.info.listen_url}/${kbnode_id}/api/nodeinfo`;
    console.info(`Checking whether node ${kbnode_id} is accessible from this location... ${check_url}`);
    get_json(check_url, function(err, resp2) {
      var accessible = false;
      if ((!err) && (resp2.info) && ((resp2.info.kbnode_id||resp2.info.node_id) == kbnode_id))
        accessible = true;
      callback(null, resp, accessible);
    });
  });
}

function get_json(url, callback) {
  $.ajax({
    url: url,
    dataType: 'json',
    success: function(data) {
      callback(null, data);
    },
    error: function(err) {
      callback('Error getting: ' + url);
    }
  });
}

function parse_url_params() {
  var match;
  var pl = /\+/g; // Regex for replacing addition symbol with a space
  var search = /([^&=]+)=?([^&]*)/g;
  var decode = function(s) {
    return decodeURIComponent(s.replace(pl, " "));
  };
  var query = window.location.search.substring(1);
  var url_params = {};
  while (match = search.exec(query))
    url_params[decode(match[1])] = decode(match[2]);
  return url_params;
}