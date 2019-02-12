import os
import traceback
import threading
import time

# invokeFunction('{callback_id_string}', [arg1,arg2], {kwargs})
vdomr_global = dict(
    mode='server',  # colab, jp_proxy_widget, server, or pywebview -- by default we are in server mode
    invokable_functions={},  # for mode=jp_proxy_widget, server, or pywebview
    jp_widget=None  # for mode=jp_proxy_widget
)

default_session = dict(javascript_to_execute=[])
vdomr_server_global = dict(
    sessions=dict(default=default_session),
    current_session=default_session
)


def _set_server_session(session_id):
    if session_id not in vdomr_server_global['sessions']:
        vdomr_server_global['sessions'][session_id] = dict(
            javascript_to_execute=[])
    vdomr_server_global['current_session'] = vdomr_server_global['sessions'][session_id]


jp_proxy_widget_invokable_functions = {}


def invoke_callback(callback_id, argument_list=[], kwargs={}):
    if callback_id not in vdomr_global['invokable_functions']:
        raise Exception('No callback with id: ' + callback_id)
    f = vdomr_global['invokable_functions'][callback_id]
    return f(*argument_list, **kwargs)


def register_callback(callback_id, callback):
    def the_callback(*args, **kwargs):
        try:
            callback(*args, **kwargs)
        except Exception as err:
            traceback.print_exc()
            print('Error: ', err)
    if vdomr_global['mode'] == 'colab':
        from google.colab import output as colab_output
        colab_output.register_callback(callback_id, the_callback)
        exec_javascript(
            'window.vdomr_invokeFunction=google.colab.kernel.invokeFunction')
    elif (vdomr_global['mode'] == 'jp_proxy_widget') or (vdomr_global['mode'] == 'server') or (vdomr_global['mode'] == 'pywebview'):
        vdomr_global['invokable_functions'][callback_id] = the_callback


def exec_javascript(js):
    if vdomr_global['mode'] == 'colab':
        from IPython.display import Javascript
        display(Javascript(js))
    elif vdomr_global['mode'] == 'jp_proxy_widget':
        vdomr_global['jp_widget'].js_init(js)
    elif vdomr_global['mode'] == 'server':
        SS = vdomr_server_global['current_session']
        if SS:
            SS['javascript_to_execute'].append(js)
        else:
            print('Warning: current session is not set. Unable to execute javascript.')
    elif vdomr_global['mode'] == 'pywebview':
        import webview
        webview.evaluate_js(js)
    else:
        from IPython.display import Javascript
        display(Javascript(js))


def _take_javascript_to_execute():
    SS = vdomr_server_global['current_session']
    if len(SS['javascript_to_execute']) == 0:
        return None
    js = '\n'.join(SS['javascript_to_execute'])
    SS['javascript_to_execute'] = []
    return js


def _found_colab():
    try:
        from google.colab import output as colab_output
        return True
    except:
        return False


def _found_jp_proxy_widget():
    try:
        import jp_proxy_widget
        return True
    except:
        return False


def _determine_mode_from_env():
    # Note: this is tricky because we might be in a local runtime on colab.
    # if os.environ.get('VDOMR_MODE', '') == 'JP_PROXY_WIDGET':
    #     print('vdomr: using jp_proxy_widget because of VDOMR_MODE environment variable')
    #     return 'jp_proxy_widget'
    # if os.environ.get('VDOMR_MODE', '') == 'COLAB':
    #     print('vdomr: using colab because of VDOMR_MODE environment variable')
    #     return 'colab'
    # if os.environ.get('VDOMR_MODE', '') == 'SERVER':
    #     print('vdomr: using SERVER mode because of VDOMR_MODE environment variable')
    #     return 'server'
    # if _found_jp_proxy_widget():
    #     if _found_colab():
    #         print(
    #             'vdomr: unable to determine whether to use jp_proxy_widget or google colab')
    #         print(
    #             'You should set the environment variable VDOMR_MODE to JP_PROXY_WIDGET or COLAB')
    #         return ''
    #     print('vdomr: using jp_proxy_widget')
    #     return 'jp_proxy_widget'
    # if _found_colab():
    #     print('vdomr: using colab')
    #     return 'colab'
    # print('vdomr: unable to import jp_proxy_widget or google.colab.colab_output')
    # # Note: this is tricky because we might be in a local runtime on colab.

    return None


def config_jupyter():
    vdomr_global['mode'] = 'jp_proxy_widget'

    import jp_proxy_widget
    jp_widget = jp_proxy_widget.JSProxyWidget()
    jp_widget.element.html("<span id=jp_widget_empty></span>")
    jp_widget.js_init("""
    // Attach the callback to the global window object so
    // you can find it from anywhere:
    window.vdomr_invokeFunction = invokeFunction;
    """, invokeFunction=invoke_callback)
    vdomr_global['jp_widget'] = jp_widget
    display(jp_widget)


def config_colab():
    vdomr_global['mode'] = 'colab'


def config_server():
    vdomr_global['mode'] = 'server'


def config_pywebview():
    vdomr_global['mode'] = 'pywebview'


class PyWebViewApi():
    def __init__(self):
        pass

    def invokeFunction(self, x):
        callback_id = x['callback_id']
        args = x['args']
        kwargs = x['kwargs']
        import webview
        webview.evaluate_js('window.show_overlay();')
        try:
            invoke_callback(callback_id, argument_list=args, kwargs=kwargs)
        except:
            traceback.print_exc()
            pass
        webview.evaluate_js('window.hide_overlay();')


def pywebview_start(*, root, title):
    try:
        import webview
    except:
        raise Exception(
            'Cannot import webview. Perhaps you need to install pywebview via: pip install pywebview')

    config_pywebview()

    def load_html():
        html = """
        <html>
        <head>
        <style>
        .overlay {
            background-color: rgba(1, 1, 1, 0.2);
            color:white;
            font-size:24px;
            bottom: 0;
            left: 0;
            position: fixed;
            right: 0;
            top: 0;
            text-align: center;
            padding: 40px;
        }
        </style>
        </head>
        <body>
        <div id=overlay class=overlay style="visibility:hidden">Please wait...</div>
        {content}
        </body>
        """
        html = html.replace('{content}', root._repr_html_())
        webview.load_html(html)
        script = """
        window.show_overlay=function() {
            document.getElementById('overlay').style.visibility='visible'
        }
        window.hide_overlay=function() {
            document.getElementById('overlay').style.visibility='hidden'
        }
        window.vdomr_invokeFunction=function(callback_id,args,kwargs) {
            console.log('vdomr_invokeFunction',callback_id,args,kwargs);

            setTimeout(function() {
                window.pywebview.api.invokeFunction({callback_id:callback_id,args:args,kwargs:kwargs});
            },0); // the timeout might be important to prevent crashes of pywebview
        }
        """
        webview.evaluate_js(script)
        js = _take_javascript_to_execute()
        webview.evaluate_js(js)

    t = threading.Thread(target=load_html)
    t.start()

    api = PyWebViewApi()
    webview.create_window(title, js_api=api, min_size=(600, 450), debug=True)


def mode():
    return vdomr_global['mode']


if os.environ.get('VDOMR_MODE', '') == 'JP_PROXY_WIDGET':
    print('vdomr: using jp_proxy_widget because of VDOMR_MODE environment variable')
    config_jupyter()

if os.environ.get('VDOMR_MODE', '') == 'COLAB':
    print('vdomr: using colab because of VDOMR_MODE environment variable')
    config_colab()

if os.environ.get('VDOMR_MODE', '') == 'SERVER':
    print('vdomr: using SERVER mode because of VDOMR_MODE environment variable')
    config_server()

if os.environ.get('VDOMR_MODE', '') == 'PYWEBVIEW':
    print('vdomr: using PYWEBVIEW mode because of VDOMR_MODE environment variable')
    config_pywebview()
