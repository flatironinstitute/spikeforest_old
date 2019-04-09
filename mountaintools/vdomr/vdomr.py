import os
import traceback
import threading
import time
import sys
import multiprocessing
import mtlogging
import uuid

# invokeFunction('{callback_id_string}', [arg1,arg2], {kwargs})
vdomr_global = dict(
    mode='server',  # colab, jp_proxy_widget, server, or pyqt5 -- by default we are in server mode
    invokable_functions={},  # for mode=jp_proxy_widget, server, or pyqt5
    jp_widget=None,  # for mode=jp_proxy_widget
    pyqt5_worker_process=False, # for mode=pyqt5 (in the worker process)
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
        from google.colab import output as colab_output # pylint: disable=import-error
        colab_output.register_callback(callback_id, the_callback)
        exec_javascript(
            'window.vdomr_invokeFunction=google.colab.kernel.invokeFunction')
    elif (vdomr_global['mode'] == 'jp_proxy_widget') or (vdomr_global['mode'] == 'server') or (vdomr_global['mode'] == 'pyqt5'):
        vdomr_global['invokable_functions'][callback_id] = the_callback
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
    vdomr_global['queued_javascript'].append(js)

def _exec_queued_javascript():
    for js in vdomr_global['queued_javascript']:
        exec_javascript(js)
    vdomr_global['queued_javascript']=[]

def exec_javascript(js):
    if vdomr_global['mode'] == 'colab':
        from IPython.display import Javascript
        display(Javascript(js)) # pylint: disable=undefined-variable
    elif vdomr_global['mode'] == 'jp_proxy_widget':
        vdomr_global['jp_widget'].js_init(js)
    elif vdomr_global['mode'] == 'server':
        SS = vdomr_server_global['current_session']
        if SS:
            SS['javascript_to_execute'].append(js)
        else:
            print('Warning: current session is not set. Unable to execute javascript.')
    elif vdomr_global['mode'] == 'pyqt5':
        if vdomr_global['pyqt5_worker_process']:
            if vdomr_global['pyqt5_connection_to_gui']:
                vdomr_global['pyqt5_connection_to_gui'].send(dict(
                    message='exec_javascript',
                    js=js
                ))
            else:
                SS = vdomr_server_global['current_session']
                SS['javascript_to_execute'].append(js)
        else:
            vdomr_global['pyqt5_view'].page().runJavaScript(js)
    else:
        from IPython.display import Javascript
        display(Javascript(js)) # pylint: disable=undefined-variable


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
    display(jp_widget) # pylint: disable=undefined-variable


def config_colab():
    vdomr_global['mode'] = 'colab'


def config_server():
    vdomr_global['mode'] = 'server'


def config_pyqt5():
    vdomr_global['mode'] = 'pyqt5'


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

def pyqt5_start(*, APP, title):
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
                // we do the following so we can get all console.log messages on the python console
                {script}
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

            script = """
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
            """
            html = html.replace('{script}', script)

            self.page().setHtml(html)
    if title is not None:
        app = QApplication([title])
    else:
        app = QApplication([])

    connection_to_worker, connection_to_gui = multiprocessing.Pipe()
    process = multiprocessing.Process(target=_pyqt5_worker_process, args=(APP, connection_to_gui))
    process.start()
    try:
        root_html = connection_to_worker.recv()
        size = connection_to_worker.recv()

        view = VdomrWebView(root_html=root_html, title=title, connection_to_worker=connection_to_worker)
        vdomr_global['pyqt5_view'] = view
        if size:
            view.resize(size[0], size[1])
        view.show()
        timer = time.time()
        while True:
            # running in the gui process
            app.processEvents()
            if time.time() - timer > 0.5: # need to wait a bit before executing javascript on the view
                if connection_to_worker.poll():
                    x = connection_to_worker.recv()
                    if x['message'] == 'exec_javascript':
                        exec_javascript(x['js'])
                    elif x['message'] == 'ok':
                        exec_javascript('window.hide_overlay();')
            time.sleep(0.001)
            if not view.isVisible():
                break
    except:
        traceback.print_exc()
    process.terminate()
    # app.exec_()

def _pyqt5_worker_process(APP, connection_to_gui):
    config_pyqt5()
    vdomr_global['pyqt5_worker_process'] = True
    
    W = APP.createSession()
    root_html = W._repr_html_()
    connection_to_gui.send(root_html)
    connection_to_gui.send(W.size())

    vdomr_global['pyqt5_connection_to_gui'] = connection_to_gui

    while True:
        js = _take_javascript_to_execute()
        if js is None:
            break
        exec_javascript(js)
    
    while True:
        if connection_to_gui.poll():
            x = connection_to_gui.recv()
            if x['message'] == 'invokeFunction':
                callback_id = x['callback_id']
                args = x['args']
                kwargs = x['kwargs']
                try:
                    invoke_callback(callback_id, argument_list=args, kwargs=kwargs)
                except:
                    traceback.print_exc()
                    pass
                connection_to_gui.send(dict(message='ok'))
        time.sleep(0.001)

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

if os.environ.get('VDOMR_MODE', '') == 'PYQT5':
    print('vdomr: using PYQT5 mode because of VDOMR_MODE environment variable')
    config_pyqt5()
