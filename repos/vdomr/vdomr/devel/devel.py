from IPython.display import HTML
import os
import vdomr as vd
import base64


def loadBootstrap():
    url = 'https://maxcdn.bootstrapcdn.com/bootstrap/3.3.7/css/bootstrap.min.css'
    integrity = 'sha384-BVYiiSIFeK1dGmJRAkycuHAHRg32OmUcww7on3RYdg4Va+PmSTsz/K68vbdEjh4u'
    crossorigin = 'anonymous'
    loadCss(url=url, integrity=integrity, crossorigin=crossorigin)

# use one of url, path, css


def loadCss(*, url=None, path=None, css=None, integrity=None, crossorigin=None):
    if path:
        with open(path) as f:
            css = f.read()
        loadCss(css=css)
        return
    if css:
        js = """
    let style = document.createElement( "style" );
    style.appendChild(document.createTextNode(atob('{css_b64}')));
    document.getElementsByTagName( "head" )[0].appendChild( style );
    """
        css_b64 = base64.b64encode(css.encode('utf-8')).decode()
        js = css_b64.join(js.split('{css_b64}'))
        loadJavascript(js=js)

        # display(HTML('<style>{}</style>'.format(css)))
        return
    if url:
        attrs = []
        # if integrity:
        #  attrs.append('integrity={}'.format(integrity))
        # if crossorigin:
        #  attrs.append('crossorigin={}'.format(crossorigin))
        html = '<link rel="stylesheet" href="{}" {}'.format(
            url, ' '.join(attrs))

        js = """
    let link = document.createElement( "link" );
    link.href = '{url}';
    link.type = "text/css";
    link.rel = "stylesheet";

    document.getElementsByTagName( "head" )[0].appendChild( link );
    """
        js = url.join(js.split('{url}'))
        loadJavascript(js=js)
        # display(HTML(html))


loaded_javascript_files = {}

# use one of url, path, js


def loadJavascript(*, url=None, path=None, js=None, delay=None):
    if path:
        modified_timestamp = os.path.getmtime(path)
        colab_mode = (vd.mode() == 'colab')
        # if (not colab_mode) and (path in loaded_javascript_files):
        #  if loaded_javascript_files[path]['mtime']==modified_timestamp:
        # already loaded
        #    return
        with open(path) as f:
            js = f.read()
        loadJavascript(js=js, delay=delay)
        # loaded_javascript_files[path]=dict(mtime=modified_timestamp)
        return
    if js:
        if delay is not None:
            js2 = """
      setTimeout(function() {
        {js}
      },{delay})
      """
            js2 = str(delay).join(js2.split('{delay}'))
            js2 = js.join(js2.split('{js}'))
            js = js2
        js = '{\n'+js+'\n}'
        vd.exec_javascript(js)
        return
    if url:
        colab_mode = (vd.mode() == 'colab')
        # if (not colab_mode) and (url in loaded_javascript_files):
        # already loaded
        #  return
        if delay is not None:
            raise Exception('Cannot use delay with url parameter')

        js0 = """
    let script = document.createElement( "script" );
    script.src = '{url}';

    document.getElementsByTagName( "head" )[0].appendChild( script );
    """
        js0 = url.join(js0.split('{url}'))
        loadJavascript(js=js0)

        # display(HTML('<script src="{}"></script>'.format(url)))
        # loaded_javascript_files[path]=dict(mtime=True)
