exports.KBNodeInfoWidget = KBNodeInfoWidget;

function KBNodeInfoWidget() {
  this.element = function() {
    return m_element;
  };
  this.setKBNodeId = function(id) {
    setKBNodeId(id);
  };
  this.setKBHubUrl = function(url) {
    setKBHubUrl(url);
  };
  this.setMaxWidth = function(max_width) {
    m_max_width = max_width;
    refresh();
  };

  const m_element = $(`
		<span>
			<table class="table">
			</table>
		</span>
	`);

  let m_kbhub_url = '';
  let m_kbnode_id = '';
  let m_info = null;
  let m_parent_hub_info = null;
  let m_child_hubs = null;
  let m_child_shares = null;
  let m_metrics = null;
  let m_max_width = 500;

  function setKBHubUrl(url) {
    if (m_kbhub_url == url) return;
    m_kbhub_url = url;
    update_info();
  }

  function setKBNodeId(id) {
    if (m_kbnode_id == id) return;
    m_kbnode_id = id;
    update_info();
  }

  function update_info() {
    m_info = null;
    refresh();
    if ((!m_kbnode_id) || (!m_kbhub_url)) {
      return;
    }
    let url = `${m_kbhub_url}/${m_kbnode_id}/api/nodeinfo`;
    $.getJSON(url, {}, function(resp) {
      m_info = resp.info || {};
      m_parent_hub_info = resp.parent_hub_info || null;
      m_child_shares = resp.child_shares || null;
      m_child_hubs = resp.child_hubs || null;
      m_metrics = resp.metrics || null;
      refresh();
    });
  }

  function refresh() {
    let table = m_element.find('table');
    table.empty();

    if (!m_info) return;

    let parent_info = m_parent_hub_info || null;

    let tablerows = [];
    tablerows.push({
      label: 'Name',
      value: `${m_info.name} (${m_info.kbnode_id||m_info.node_id})`
    });
    tablerows.push({
      label: 'Type',
      value: m_info.kbnode_type||m_info.node_type
    });
    tablerows.push({
      label: 'owner',
      value: `${m_info.owner} (${m_info.owner_email})`
    });
    tablerows.push({
      label: 'Description',
      value: m_info.description
    });
    if (parent_info) {
      tablerows.push({
        label: 'Parent hub',
        value: `${parent_info.name} (<a href=# id=open_parent_hub>${parent_info.kbnode_id||parent_info.node_id}</a>)`
      });
    } else {
      tablerows.push({
        label: 'Parent hub',
        value: '[None]'
      });
    }

    if ((m_child_shares)&&(m_child_shares)) {
      tablerows.push({
        label: 'Num. child hubs/shares',
        value: `${Object.keys(m_child_hubs).length}/${Object.keys(m_child_shares).length}`
      });
    }

    if (m_metrics) {
      tablerows.push({
        label: 'Metrics',
        value: JSON.stringify(m_metrics, null, 4).split('\n').join('<br>').split(' ').join('&nbsp;')
      });
    }

    tablerows.push({
      label: 'Info',
      value: JSON.stringify(m_info, null, 4).split('\n').join('<br>').split(' ').join('&nbsp;')
    });

    if (parent_info) {
      tablerows.push({
        label: 'Parent info',
        value: JSON.stringify(m_parent_hub_info, null, 4).split('\n').join('<br>').split(' ').join('&nbsp;')
      });
    }



    for (let i in tablerows) {
      let row = tablerows[i];
      let tr = $('<tr></tr>');
      tr.append(`<th id=label">${row.label}</th>`);
      tr.append(`<td id=value>${row.value}</td>`);
      tr.find('#label').css({
        'max-width': 100
      });
      tr.find('#value').css({
        'max-width': m_max_width - 100 - 50
      });
      table.append(tr);
    }

    table.find('#open_parent_hub').click(function() {
      let query=window.query||{};
      let url=`?hub=${parent_info.kbnode_id||parent_info.node_id}`;
      if (query.kbucket_url)
        url+=`&kbucket_url=${query.kbucket_url}`;
      window.location.href = url;
    });
  }
}