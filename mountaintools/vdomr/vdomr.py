import os
import traceback
import threading
import time
import sys

# invokeFunction('{callback_id_string}', [arg1,arg2], {kwargs})
vdomr_global = dict(
    mode='server',  # colab, jp_proxy_widget, server, or pyqt5 -- by default we are in server mode
    invokable_functions={},  # for mode=jp_proxy_widget, server, or pyqt5
    jp_widget=None,  # for mode=jp_proxy_widget
    pyqt5_view=None  # for mode=pyqt5
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
    elif (vdomr_global['mode'] == 'jp_proxy_widget') or (vdomr_global['mode'] == 'server') or (vdomr_global['mode'] == 'pyqt5'):
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
    elif vdomr_global['mode'] == 'pyqt5':
        if vdomr_global['pyqt5_view']:
            vdomr_global['pyqt5_view'].page().runJavaScript(js)
        else:
            SS = vdomr_server_global['current_session']
            SS['javascript_to_execute'].append(js)
    else:
        from IPython.display import Javascript
        display(Javascript(js))


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
    display(jp_widget)


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


def pyqt5_start(*, root, title):
    try:
        # from PyQt5.QtCore import *
        from PyQt5.QtCore import QObject, QVariant, pyqtSlot
        from PyQt5.QtWebChannel import QWebChannel
        from PyQt5.QtWebEngineWidgets import QWebEngineView
        from PyQt5.QtWidgets import QApplication
    except:
        raise Exception(
            'Cannot import PyQt5 and friends. Perhaps you need to install PyQt5 and QtWebEngine')

    class PyQt5Api(QObject):
        def __init__(self):
            super(PyQt5Api, self).__init__()

        @pyqtSlot(QVariant, result=QVariant)
        def invokeFunction(self, x):
            callback_id = x['callback_id']
            args = x['args']
            kwargs = x['kwargs']
            try:
                invoke_callback(callback_id, argument_list=args, kwargs=kwargs)
            except:
                traceback.print_exc()
                pass
            return None

        @pyqtSlot(str, result=QVariant)
        def console_log(self, a):
            print('JS:', a)
            return None

    class VdomrWebView(QWebEngineView):
        def __init__(self, root):
            super(VdomrWebView, self).__init__()

            self._root = root

            self._channel = QWebChannel()
            self._pyqt5_api = PyQt5Api()
            self._channel.registerObject('pyqt5_api', self._pyqt5_api)
            self.page().setWebChannel(self._channel)

            html = """
                <html>
                <head>
                <style>
                .overlay {
                    background-color: rgba(1, 1, 1, 0.8);
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
                <script src="qrc:///qtwebchannel/qwebchannel.js"></script>
                <script>
                // we do the following so we can get all console.log messages on the python console
                console.log=console.error;
                {script}
                </script>
                </head>
                <body>
                <div id=overlay class=overlay style="visibility:hidden">Please wait...</div>
                {content}
                <script language="JavaScript">
                    new QWebChannel(qt.webChannelTransport, function (channel) {
                        window.pyqt5_api = channel.objects.pyqt5_api;
                        /*
                        // instead of doing the following, we map console.log to console.error above
                        console.log=function(a,b,c) {
                            let txt;
                            if (c) txt=a+' '+b+' '+c;
                            else if (b) txt=a+' '+b;
                            else txt=a+'';
                            pyqt5_api.console_log(txt);
                        }
                        */
                    });
                </script>
                </body>
            """
            html = html.replace('{content}', root._repr_html_())

            script = """
                window.show_overlay=function() {
                    document.getElementById('overlay').style.visibility='visible'
                }
                window.hide_overlay=function() {
                    document.getElementById('overlay').style.visibility='hidden'
                }
                window.vdomr_invokeFunction=function(callback_id,args,kwargs) {
                    window.show_overlay();
                    setTimeout(function() {
                        pyqt5_api.invokeFunction({callback_id:callback_id,args:args,kwargs:kwargs});
                        window.hide_overlay();
                    },100); // the timeout might be important to prevent crashes, not sure
                }
            """
            while True:
                js = _take_javascript_to_execute()
                if js is None:
                    break
                script = script+'\n'+js
            html = html.replace('{script}', script)

            self.page().setHtml(html)

    app = QApplication([])
    view = VdomrWebView(root=root)
    vdomr_global['pyqt5_view'] = view
    view.show()
    app.exec_()

    # webview.evaluate_js(script)
    # js = _take_javascript_to_execute()
    # webview.evaluate_js(js)


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
