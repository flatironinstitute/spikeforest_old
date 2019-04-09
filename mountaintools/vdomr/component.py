import base64
import uuid
import abc

from .vdomr import exec_javascript, _queue_javascript, _exec_queued_javascript


class Component(object):
    def __init__(self):
        self._component_id = str(uuid.uuid4())
        self._div_id = 'component-div-'+self._component_id

    @abc.abstractmethod
    def render(self):
        return None

    def postRenderScript(self):
        return None

    def componentId(self):
        return self._component_id

    def refresh(self):
        html=self._render_and_get_html()
        html_encoded = base64.b64encode(html.encode('utf-8')).decode('utf-8')
        js = "{{var elmt=document.getElementById('{}'); if (elmt) elmt.innerHTML=atob('{}');}}".format(
            self._div_id, html_encoded)
        exec_javascript(js)
        _exec_queued_javascript()

    def to_html(self):
        return self._repr_html_()

    def _repr_html_(self):
        html=self._render_and_get_html()
        return '<div id={}>'.format(self._div_id)+html+'</div>'

    def _render_and_get_html(self):
        html = self.render().to_html()
        js = self.postRenderScript() # pylint: disable=assignment-from-none
        if js:
            # Note the following has a terrible race condition
            js2 = """
            (function() {
                {js}
            })()
            """
            js2=js2.replace('{js}', js)
            _queue_javascript(js2)
        return html
