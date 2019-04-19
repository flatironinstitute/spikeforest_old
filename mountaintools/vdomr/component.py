import base64
import uuid
import abc

from .vdomr import exec_javascript, _queue_javascript, _exec_queued_javascript, set_timeout, mode, _exec_queued_javascript


class Component(object):
    def __init__(self):
        self._component_id = str(uuid.uuid4())
        self._div_id = 'component-div-'+self._component_id
        self._render_code = 0

    @abc.abstractmethod
    def render(self):
        return None

    def postRenderScript(self):
        return None

    def componentId(self):
        return self._component_id

    def refresh(self):
        js = """
        ((window.vdomr_components||{})['{component_id}']||{}).ready=false;
        """
        js = js.replace('{component_id}', self.componentId())
        exec_javascript(js)

        html=self._render_and_get_html()
        html_encoded = base64.b64encode(html.encode('utf-8')).decode('utf-8')
        
        js = """
        (function() {
            let ee = document.getElementById('{div_id}');
            if (ee) {
                ee.innerHTML=atob('{html_encoded}');
            }
        })();
        """
        js = js.replace('{div_id}', self._div_id)
        js = js.replace('{html_encoded}', html_encoded)
        exec_javascript(js)

    def executeJavascript(self, js, **kwargs):
        # important to wrap this in setTimeout call so that the _render_and_get_html gets executed first
        js2 = """
        setTimeout(function() {
            window.vdomr_on_component_ready('{component_id}', function() {
                let elmt=document.getElementById('{div_id}');
                if (elmt) {
                    {js}
                }
                else {
                    // console.warn('WARNING: unable to execute javascript for component because element was not found.');
                }
            });
        },0);
        """
        js2=js2.replace('{div_id}', self._div_id)
        js2=js2.replace('{component_id}', self.componentId())
        js2=js2.replace('{js}', js)
        exec_javascript(js2)

    def to_html(self):
        return self._repr_html_()

    def _repr_html_(self):
        self._render_code = self._render_code + 1
        html=self._render_and_get_html()
        return '<div id={} data-vdomr-render-code={}>'.format(self._div_id, self._render_code)+html+'</div>'

    def _render_and_get_html(self):
        self._render_in_progress = True
        html = self.render().to_html()
        js = self.postRenderScript() # pylint: disable=assignment-from-none
        if not js:
            js='// no post-render javascript'
        # important to wrap this in setTimeout call so that the refresh gets executed first
        js2 = """
        window.vdomr_set_component_ready('{component_id}', false);
        setTimeout(function() {
            window.vdomr_set_component_ready('{component_id}', false);
            window.vdomr_on_element_ready('{div_id}', '{render_code}', function() {
                var elmt=document.getElementById('{div_id}');
                if (elmt) {
                    // important to only run the javascript if we find the element on the page!!
                    {js}
                    window.vdomr_trigger_on_ready_handlers('{component_id}');
                    window.vdomr_set_component_ready('{component_id}', true);
                }
                else {
                    console.warn('WARNING: unable to execute post-render javascript for component because element was not found.');
                }
            });
        }, 0);
        """
        js2=js2.replace('{js}', js)
        js2=js2.replace('{div_id}', self._div_id)
        js2=js2.replace('{render_code}', str(self._render_code))
        js2=js2.replace('{component_id}', self.componentId())
        exec_javascript(js2)
        return html
