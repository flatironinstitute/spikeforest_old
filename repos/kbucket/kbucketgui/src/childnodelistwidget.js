exports.ChildNodeListWidget = ChildNodeListWidget;

function ChildNodeListWidget() {
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
  let m_child_hubs = null;
  let m_child_shares = null;
  let m_max_width = 1000;

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
      m_child_shares = resp.child_shares || resp.child_leaf_nodes || null;
      m_child_hubs = resp.child_hubs || null;
      refresh();
    });
  }

  function refresh() {
    let table = m_element.find('table');
    table.empty();

    if ((!m_child_hubs)||(!m_child_shares)) return;

    {
      let tr = $('<tr></tr>');
      tr.append(`<th id=label>Child hubs</th>`);
      tr.append(`<td><span id=child_hubs></span></td>`);
      tr.find('#label').css({
        'max-width': 100
      });
      tr.find('#value').css({
        'max-width': m_max_width - 100 - 50
      });
      table.append(tr);
    }
    {
      let tr = $('<tr></tr>');
      tr.append(`<th id=label>Child shares</th>`);
      tr.append(`<td><span id=child_shares></span></td>`);
      tr.find('#label').css({
        'max-width': 100
      });
      tr.find('#value').css({
        'max-width': m_max_width - 100 - 50
      });
      table.append(tr);
    }

    for (let id in m_child_hubs) {
      let elmt=$(`<span>${m_child_hubs[id].name} (<a class=open_child_hub href=# child_hub_id=${id}>${id}</a>)</span>`);
      table.find('#child_hubs').append(elmt);
      table.find('#child_hubs').append('&nbsp;&nbsp;');
    }

    for (let id in m_child_shares) {
      let elmt=$(`<span>${m_child_shares[id].name} (<a class=open_child_share href=# child_share_id=${id}>${id}</a>)</span>`);
      table.find('#child_shares').append(elmt);
      table.find('#child_shares').append('&nbsp;&nbsp;');
    }

    table.find('.open_child_hub').click(function() {
      let id=$(this).attr('child_hub_id');
      let query=window.query||{};
      let url=`?hub=${id}`;
      if (query.kbucket_url)
        url+=`&kbucket_url=${query.kbucket_url}`;
      window.location.href = url;
    });

    table.find('.open_child_share').click(function() {
      let id=$(this).attr('child_share_id');
      let query=window.query||{};
      let url=`?share=${id}`;
      if (query.kbucket_url)
        url+=`&kbucket_url=${query.kbucket_url}`;
      window.location.href = url;
    });
  }
}