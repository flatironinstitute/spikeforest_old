exports.KBShareBrowser = KBShareBrowser;

var FileBrowserWidget = require(__dirname + '/filebrowserwidget.js').FileBrowserWidget;
var KBNodeInfoWidget = require(__dirname + '/kbnodeinfowidget.js').KBNodeInfoWidget;

function KBShareBrowser() {
  this.element = function() {
    return m_element;
  };
  this.setKBHubUrl = function(url) {
    setKBHubUrl(url);
  };
  this.setKBShareId = function(id) {
    setKBShareId(id);
  };

  var m_kbhub_url = '';
  var m_kbshare_id = '';
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
							<div class="ml-item-content" id="file_browser" style="margin:10px; background:">
							</div>
						</div>
					</div>
				</div
			</div>
		</span>
	`);

  var m_file_browser_widget = new FileBrowserWidget();
  var m_info_widget = new KBNodeInfoWidget();
  m_info_widget.setMaxWidth(m_left_panel_width);

  m_element.find('#file_browser').append(m_file_browser_widget.element());
  m_element.find('#left_panel').append(m_info_widget.element());

  function setKBHubUrl(url) {
    if (m_kbhub_url == url) return;
    m_kbhub_url = url;
    update();
  }

  function setKBShareId(id) {
    if (m_kbshare_id == id) return;
    m_kbshare_id = id;
    update();
  }

  function update() {
    m_file_browser_widget.setKBHubUrl(m_kbhub_url);
    m_file_browser_widget.setKBShareId(m_kbshare_id);
    m_file_browser_widget.setRootLabel(`kbucket://${m_kbshare_id}`);
    m_info_widget.setKBHubUrl(m_kbhub_url);
    m_info_widget.setKBNodeId(m_kbshare_id);
  }
}