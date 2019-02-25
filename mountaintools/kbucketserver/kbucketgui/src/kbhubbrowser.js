exports.KBHubBrowser = KBHubBrowser;

var ChildNodeListWidget = require(__dirname + '/childnodelistwidget.js').ChildNodeListWidget;
var KBNodeInfoWidget = require(__dirname+'/kbnodeinfowidget.js').KBNodeInfoWidget;

function KBHubBrowser() {
  this.element = function() {
    return m_element;
  };
  this.setKBHubUrl=function(url) {
    setKBHubUrl(url);
  }
  this.setKBHubId = function(id) {
    setKBHubId(id);
  };

  var m_kbhub_id = '';
  var m_kbhub_url='';
  var m_left_panel_width = 600;

  var m_element = $(`
		<span>
			<div class="ml-vlayout">
				<div class="ml-vlayout-item" style="flex:20px 0 0">
					<span id=top_bar style="padding-left:20px">

					</span>
				</div>
				<div class="ml-vlayout-item" style="flex:1">
					<div class="ml-hlayout">
						<div class="ml-hlayout-item" style="flex:${m_left_panel_width}px 0 0">
							<div class="ml-item-content" id="left_panel" style="margin:10px; background:">

							</div>
						</div>
						<div class="ml-hlayout-item" style="flex:1">
							<div class="ml-item-content" id="child_node_list" style="margin:10px; background:">
							</div>
						</div>
					</div>
				</div
			</div>
		</span>
	`);

  var m_child_node_list_widget = new ChildNodeListWidget();
  var m_info_widget = new KBNodeInfoWidget();
  m_info_widget.setMaxWidth(m_left_panel_width);

  m_element.find('#child_node_list').append(m_child_node_list_widget.element());
  m_element.find('#left_panel').append(m_info_widget.element());

  function setKBHubUrl(url) {
    if (m_kbhub_url==url) return;
    m_kbhub_url=url;
    m_info_widget.setKBHubUrl(url);
    m_child_node_list_widget.setKBHubUrl(url);
  }

  function setKBHubId(id) {
    if (m_kbhub_id==id) return;
    m_kbhub_id = id;
    //m_file_browser_widget.setBaseUrl(`${config.kbucket_hub_url}/${m_kbhub_id}`);
    m_info_widget.setKBNodeId(id);
    m_child_node_list_widget.setKBNodeId(id);
  }
}

