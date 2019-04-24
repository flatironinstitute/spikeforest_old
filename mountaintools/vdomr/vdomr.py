"""vdomr main module
"""

import os
import traceback
import time
import multiprocessing
import uuid
import sys

# BOOKMARK VDOMR

# MEDIUM TODO make vdomr readme and release vdomr 1.0

# invokeFunction('{callback_id_string}', [arg1,arg2], {kwargs})
VDOMR_GLOBAL = dict(
    mode='server',  # colab, jp_proxy_widget, server, or pyqt5 -- by default we are in server mode
    invokable_functions={},  # for mode=jp_proxy_widget, server, or pyqt5
    jp_widget=None,  # for mode=jp_proxy_widget
    pyqt5_worker_process=False,  # for mode=pyqt5 (in the worker process)
    pyqt5_view=None,  # for mode=pyqt5
    pyqt5_connection_to_gui=None,  # for mode=pyqt5
    queued_javascript=[]
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
    if callback_id not in VDOMR_GLOBAL['invokable_functions']:
        raise Exception('No callback with id: ' + callback_id)
    f = VDOMR_GLOBAL['invokable_functions'][callback_id]
    return f(*argument_list, **kwargs)


def register_callback(callback_id, callback):
    def the_callback(*args, **kwargs):
        try:
            callback(*args, **kwargs)
        except Exception as err:
            traceback.print_exc()
            print('Error: ', err)
    if VDOMR_GLOBAL['mode'] == 'colab':
        from google.colab import output as colab_output  # pylint: disable=import-error
        colab_output.register_callback(callback_id, the_callback)
        exec_javascript(
            'window.vdomr_invokeFunction=google.colab.kernel.invokeFunction')
    elif ((VDOMR_GLOBAL['mode'] == 'jp_proxy_widget')
          or (VDOMR_GLOBAL['mode'] == 'server') 
          or (VDOMR_GLOBAL['mode'] == 'pyqt5')):
        VDOMR_GLOBAL['invokable_functions'][callback_id] = the_callback
    ret = "(function(args, kwargs) {window.vdomr_invokeFunction('{callback_id}', args, kwargs);})"
    ret = ret.replace('{callback_id}', callback_id)
    return ret


def create_callback(callback):
    callback_id = 'callback-'+str(uuid.uuid4())
    return register_callback(callback_id, callback)


def set_timeout(callback, timeout_sec):
    timeout_callback_id = 'timeout-callback-' + str(uuid.uuid4())
    register_callback(timeout_callback_id, callback)
    js = """
    setTimeout(function() {
        window.vdomr_invokeFunction('{timeout_callback_id}', [], {})
    }, {timeout_msec});
    """
    js = js.replace('{timeout_callback_id}', timeout_callback_id)
    js = js.replace('{timeout_msec}', str(timeout_sec*1000))
    exec_javascript(js)


def _queue_javascript(js):
    VDOMR_GLOBAL['queued_javascript'].append(js)


def _exec_queued_javascript():
    queued_javascript = VDOMR_GLOBAL['queued_javascript']
    VDOMR_GLOBAL['queued_javascript'] = []
    for js in queued_javascript:
        exec_javascript(js)


def exec_javascript(js):
    _exec_queued_javascript()
    if VDOMR_GLOBAL['mode'] == 'colab':
        from IPython.display import Javascript
        display(Javascript(js))  # pylint: disable=undefined-variable
    elif VDOMR_GLOBAL['mode'] == 'jp_proxy_widget':
        VDOMR_GLOBAL['jp_widget'].js_init(js)
    elif VDOMR_GLOBAL['mode'] == 'server':
        SS = vdomr_server_global['current_session']
        if SS:
            SS['javascript_to_execute'].append(js)
        else:
            print('Warning: current session is not set. Unable to execute javascript.')
    elif VDOMR_GLOBAL['mode'] == 'pyqt5':
        if VDOMR_GLOBAL['pyqt5_worker_process']:
            if VDOMR_GLOBAL['pyqt5_connection_to_gui']:
                VDOMR_GLOBAL['pyqt5_connection_to_gui'].send(dict(
                    message='exec_javascript',
                    js=js
                ))
            else:
                SS = vdomr_server_global['current_session']
                SS['javascript_to_execute'].append(js)
        else:
            VDOMR_GLOBAL['pyqt5_view'].page().runJavaScript(js)
    else:
        from IPython.display import Javascript
        display(Javascript(js))  # pylint: disable=undefined-variable


def _take_javascript_to_execute():
    SS = vdomr_server_global['current_session']
    if len(SS['javascript_to_execute']) == 0:
        return None
    js = SS['javascript_to_execute'][0]
    SS['javascript_to_execute'] = SS['javascript_to_execute'][1:]
    #js = '\n'.join(SS['javascript_to_execute'])
    #SS['javascript_to_execute'] = []
    return js


def _found_colab():
    try:
        from google.colab import output as colab_output # pylint: disable=unused-import
        return True
    except ImportError:
        return False


def _found_jp_proxy_widget():
    try:
        import jp_proxy_widget # pylint: disable=unused-import
        return True
    except ImportError:
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
    VDOMR_GLOBAL['mode'] = 'jp_proxy_widget'

    import jp_proxy_widget
    jp_widget = jp_proxy_widget.JSProxyWidget()
    jp_widget.element.html("<span id=jp_widget_empty></span>")
    jp_widget.js_init("""
    // Attach the callback to the global window object so
    // you can find it from anywhere:
    window.vdomr_invokeFunction = invokeFunction;
    """, invokeFunction=invoke_callback)
    jp_widget.js_init(_get_init_javascript())  # thx, A. Morley
    # plotly tests for this but doesn't need it to do anything :/
    jp_widget.js_init("window.URL.createObjectURL = function() {};")
    VDOMR_GLOBAL['jp_widget'] = jp_widget
    display(jp_widget)  # pylint: disable=undefined-variable


def config_colab(local_runtime=False):
    VDOMR_GLOBAL['mode'] = 'colab'
    if local_runtime:
        # this is needed so that dummy "google" may be imported, and thus callbacks may be registered
        source_path=os.path.dirname(os.path.realpath(__file__))
        sys.path.append(source_path)

def init_colab():
    config_colab()
    exec_javascript(_get_init_javascript())

def config_server():
    VDOMR_GLOBAL['mode'] = 'server'


def config_pyqt5():
    VDOMR_GLOBAL['mode'] = 'pyqt5'


# class PyWebViewApi():
#     def __init__(self):
#         pass

#     def invokeFunction(self, x):
#         callback_id = x['callback_id']
#         args = x['args']
#         kwargs = x['kwargs']
#         import webview
#         webview.evaluate_js('window.show_overlay();')
#         try:
#             invoke_callback(callback_id, argument_list=args, kwargs=kwargs)
#         except:
#             traceback.print_exc()
#             pass
#         webview.evaluate_js('window.hide_overlay();')

def pyqt5_start(*, app, title):
    try:
        # from PyQt5.QtCore import *
        from PyQt5.QtCore import QObject, QVariant, pyqtSlot
        from PyQt5.QtWebChannel import QWebChannel
        from PyQt5.QtWebEngineWidgets import QWebEngineView
        from PyQt5.QtWidgets import QApplication
    except:
        raise Exception(
            'Cannot import PyQt5 and friends. Perhaps you need to install PyQt5 and QtWebEngine')

    config_pyqt5()

    class PyQt5Api(QObject):
        def __init__(self, connection_to_worker):
            super(PyQt5Api, self).__init__()
            self._connection_to_worker = connection_to_worker

        @pyqtSlot(QVariant, result=QVariant)
        def invokeFunction(self, x):
            self._connection_to_worker.send(dict(
                message='invokeFunction',
                **x
            ))

        @pyqtSlot(str, str, str, str, str, str, str, result=QVariant)
        def console_log(self, a, b='', c='', d='', e='', f='', g=''):
            print('JS:', a, b, c, d, e, f, g)
            return None

    class VdomrWebView(QWebEngineView):
        def __init__(self, root_html, title, connection_to_worker):
            super(VdomrWebView, self).__init__()

            self._root_html = root_html
            self._title = title
            self._channel = QWebChannel()
            self._pyqt5_api = PyQt5Api(connection_to_worker)
            self._channel.registerObject('pyqt5_api', self._pyqt5_api)
            self.page().setWebChannel(self._channel)

            html = """
                <html>
                <head>
                <style>
                .overlay {
                    position: fixed;
                    top: 0%;
                    left: 0%;
                    width: 100%;
                    height: 100%;
                    background-color: lightgray;
                    -moz-opacity: 0.8;
                    filter: alpha(opacity=80);
                    opacity:.80;
                    z-index:1001;
                    text-align: center;
                    font-size: 24px;
                    color:white
                }
                </style>
                <script src="qrc:///qtwebchannel/qwebchannel.js"></script>
                <script>
                window.show_overlay=function() {
                    document.getElementById('overlay').style.display='block'
                }
                window.hide_overlay=function() {
                    document.getElementById('overlay').style.display='none'
                }
                window.vdomr_invokeFunction=function(callback_id,args,kwargs) {
                    // window.show_overlay();
                    pyqt5_api.invokeFunction({callback_id:callback_id,args:args,kwargs:kwargs});
                }
                {init_js}
                </script>
                </head>
                <body>
                <div id=overlay class=overlay style="display:none">Please wait...</div>
                {content}
                <script language="JavaScript">
                    new QWebChannel(qt.webChannelTransport, function (channel) {
                        window.pyqt5_api = channel.objects.pyqt5_api;
                        
                        console.log=function(a,b,c,d,e,f,g) {
                            pyqt5_api.console_log((a||'')+'',(b||'')+'',(c||'')+'',(d||'')+'',(e||'')+'',(f||'')+'',(g||'')+'');
                        }
                        
                    });
                </script>
                </body>
            """
            html = html.replace('{content}', root_html)

            html = html.replace('{init_js}', _get_init_javascript())

            self.page().setHtml(html)
    qapp = QApplication([])

    connection_to_worker, connection_to_gui = multiprocessing.Pipe()
    process = multiprocessing.Process(
        target=_pyqt5_worker_process, args=(app, connection_to_gui))
    process.start()
    try:
        root_html = connection_to_worker.recv()
        size = connection_to_worker.recv()

        view = VdomrWebView(root_html=root_html, title=title,
                            connection_to_worker=connection_to_worker)
        if title is not None:
            view.setWindowTitle(title)
        VDOMR_GLOBAL['pyqt5_view'] = view
        if size:
            view.resize(size[0], size[1])
        view.show()
        timer = time.time()
        while True:
            # running in the gui process
            qapp.processEvents()
            if time.time() - timer > 0.5:  # need to wait a bit before executing javascript on the view
                if connection_to_worker.poll():
                    x = connection_to_worker.recv()
                    if x['message'] == 'exec_javascript':
                        exec_javascript(x['js'])
                    elif x['message'] == 'ok':
                        exec_javascript('window.hide_overlay();')
            time.sleep(0.001)
            if not view.isVisible():
                break
    except: # pylint: disable=bare-except
        traceback.print_exc()
    process.terminate()
    # qapp.exec_()


def _pyqt5_worker_process(app, connection_to_gui):
    config_pyqt5()
    VDOMR_GLOBAL['pyqt5_worker_process'] = True

    W = app.createSession()
    root_html = W._repr_html_()
    connection_to_gui.send(root_html)
    connection_to_gui.send(W.size())

    VDOMR_GLOBAL['pyqt5_connection_to_gui'] = connection_to_gui

    while True:
        js0 = _take_javascript_to_execute()
        if js0 is None:
            break
        exec_javascript(js0)

    while True:
        if connection_to_gui.poll():
            x = connection_to_gui.recv()
            if x['message'] == 'invokeFunction':
                callback_id = x['callback_id']
                args = x['args']
                kwargs = x['kwargs']
                try:
                    invoke_callback(
                        callback_id, argument_list=args, kwargs=kwargs)
                except: # pylint: disable=bare-except
                    traceback.print_exc()
                connection_to_gui.send(dict(message='ok'))
        time.sleep(0.001)


def _get_init_javascript():
    return """
    function create_vdomr_component_if_needed(component_id) {
        if (!window.vdomr_components) window.vdomr_components={};
        if (!window.vdomr_components[component_id]) {
            window.vdomr_components[component_id]={ready:false, on_ready_handlers:[]};
        }
    }
    window.vdomr_on_component_ready=function(component_id, callback) {
        create_vdomr_component_if_needed(component_id);
        if (window.vdomr_components[component_id].ready) {
            callback();
            return;
        }
        window.vdomr_components[component_id].on_ready_handlers.push(callback);
    }
    window.vdomr_on_element_ready=function(element_id, render_code, callback) {
        let num_tries=0;
        function do_check() {
            let elmt0=document.getElementById(element_id);
            if (elmt0) {
                let elmt_render_code = elmt0.getAttribute('data-vdomr-render-code');
                if (elmt_render_code == render_code) {
                    callback();
                    return;
                }
                else {
                    if (Number(elmt_render_code) > render_code) {
                        // never going to be ready -- has already been rendered
                        return;
                    }
                    // console.log('Render codes do not match', elmt_render_code, render_code);
                }
            }
            let timeout_msec=1;
            if (num_tries<1) timeout_msec=1;
            else if (num_tries<5) timeout_msec=100;
            else if (num_tries<10) timeout_msec=500;
            else {
                // console.warn('VDOMR WARNING: timeout out while waiting for element to be ready.');
                return;
            }
            num_tries=num_tries+1;
            setTimeout(do_check, timeout_msec);
        }
        do_check();
    }
    window.vdomr_set_component_ready=function(component_id, val) {
        create_vdomr_component_if_needed(component_id);
        window.vdomr_components[component_id].ready=val;
    }
    window.vdomr_trigger_on_ready_handlers=function(component_id, val) {
        create_vdomr_component_if_needed(component_id);
        let handlers=window.vdomr_components[component_id].on_ready_handlers;
        window.vdomr_components[component_id].on_ready_handlers=[];
        handlers.forEach(function(handler) {
            handler();
        });
    }
    """


def mode():
    return VDOMR_GLOBAL['mode']


if os.environ.get('VDOMR_MODE', '') == 'JP_PROXY_WIDGET':
    print('vdomr: using jp_proxy_widget because of VDOMR_MODE environment variable')
    config_jupyter()

if os.environ.get('VDOMR_MODE', '') == 'COLAB':
    print('vdomr: using colab because of VDOMR_MODE environment variable')
    config_colab()

if os.environ.get('VDOMR_MODE', '') == 'SERVER':
    print('vdomr: using SERVER mode because of VDOMR_MODE environment variable')
    config_server()

if os.environ.get('VDOMR_MODE', '') == 'PYQT5':
    print('vdomr: using PYQT5 mode because of VDOMR_MODE environment variable')
    config_pyqt5()
