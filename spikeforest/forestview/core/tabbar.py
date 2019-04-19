import vdomr as vd
import os

source_path = os.path.dirname(os.path.realpath(__file__))

class TabBar(vd.Component):
    def __init__(self):
        vd.Component.__init__(self)
        self._height = 46 # hard-coded to match css of ChromeTabs
        self._current_tab_id = None
        self._current_tab_changed_handlers = []
        self._tab_removed_handlers = []
        self._tab_labels = dict()

        vd.devel.loadJavascript(path=source_path+'/draggabilly.js')
        vd.devel.loadCss(path=source_path+'/chrome-tabs/css/chrome-tabs.css')
        vd.devel.loadCss(path=source_path+'/chrome-tabs/css/chrome-tabs-dark-theme.css')
        vd.devel.loadCss(css=_CSS)
        vd.devel.loadJavascript(path=source_path+'/chrome-tabs/js/chrome-tabs.js')

    def height(self):
        return self._height

    def onCurrentTabChanged(self, handler):
        self._current_tab_changed_handlers.append(handler)

    def onTabRemoved(self, handler):
        self._tab_removed_handlers.append(handler)

    def setCurrentTab(self, id):
        js = """
        let chromeTabs = window.chrome_tab_widgets['{component_id}'];
        let el = document.querySelector('#div-{component_id}');
        let tabEl = $(el).find('[data-tab-id={tab_id}]');
        if (tabEl)
            chromeTabs.setCurrentTab(tabEl[0]);
        """
        js = js.replace('{tab_id}', id)
        js=js.replace('{component_id}', self.componentId())
        self.executeJavascript(js=js)

    def currentTabId(self):
        return self._current_tab_id

    def addTab(self, id, label):
        js = """
        let chromeTabs = window.chrome_tab_widgets['{component_id}'];
        chromeTabs.addTab({
            id: '{id}',
            title: 'initializing...',
            favicon: false
        });
        """
        js = js.replace('{id}', id)
        js=js.replace('{component_id}', self.componentId())
        js=js.replace('{label}', label)
        self.executeJavascript(js=js)
        self._on_active_tab_changed(id)
        self.setTabLabel(id, label)
        pass

    def setTabLabel(self, id, label):
        if id in self._tab_labels:
            if label == self._tab_labels[id]:
                return
        self._tab_labels[id] = label
        js = """
        let el = document.querySelector('#div-{component_id}');
        let tabEl = $(el).find('[data-tab-id={tab_id}]');
        $(tabEl).find('.chrome-tab-title').html('{label}');
        """
        js = js.replace('{tab_id}', id)
        js=js.replace('{component_id}', self.componentId())
        js=js.replace('{label}', label)
        self.executeJavascript(js)

    def render(self):
        div=vd.div(vd.div(class_="chrome-tabs-content"), vd.div(class_="chrome-tabs-bottom-bar"), class_='chrome-tabs', id='div-'+self.componentId())
        return div

    def _on_active_tab_changed(self, id):
        if self._current_tab_id == id:
            return
        self._current_tab_id = id
        for handler in self._current_tab_changed_handlers:
            handler()

    def _on_tab_removed(self, id):
        for handler in self._tab_removed_handlers:
            handler(id)
        if id == self._current_tab_id:
            self._on_active_tab_changed(None)

    def postRenderScript(self):
        js = """
        let chromeTabs = new ChromeTabs()
        window.chrome_tab_widgets=window.chrome_tab_widgets||{};
        window.chrome_tab_widgets['{component_id}']=chromeTabs;

        let el = document.querySelector('#div-{component_id}');
        chromeTabs.init(el);
        
        el.addEventListener('activeTabChange', function(evt) {
            let id = evt.detail.tabEl.getAttribute('data-tab-id');
            {on_active_tab_changed}([],{id:id});

        });
        el.addEventListener('tabRemove', function(evt) {
            let id = evt.detail.tabEl.getAttribute('data-tab-id');
            {on_tab_removed}([],{id:id});

        });
        """
        js=js.replace('{component_id}', self.componentId())
        js=js.replace('{on_active_tab_changed}', vd.create_callback(self._on_active_tab_changed))
        js=js.replace('{on_tab_removed}', vd.create_callback(self._on_tab_removed))
        return js

_CSS = """
.chrome-tabs .chrome-tab {
width: 258px
}

.chrome-tabs .chrome-tab:nth-child(1) {
transform: translate3d(0px, 0, 0)
}

.chrome-tabs .chrome-tab:nth-child(2) {
transform: translate3d(239px, 0, 0)
}
"""