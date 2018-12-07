import uuid
import os

# invokeFunction('{callback_id_string}', [arg1,arg2], {kwargs})
vdomr_global=dict(
    jp_invokable_functions={},
    jp_widget=None,
    mode=None
)

jp_proxy_widget_invokable_functions = {}
def jp_proxy_widget_invokeFunction(identifier, argument_list, kwargs):
    f = vdomr_global['jp_invokable_functions'][identifier]
    f(*argument_list, **kwargs)

def register_callback(callback_id,callback):
    if vdomr_global['mode']=='colab':
        from google.colab import output as colab_output
        colab_output.register_callback(callback_id,callback)
        exec_javascript('window.vdomr_invokeFunction=google.colab.kernel.invokeFunction')
    elif vdomr_global['mode']=='jp_proxy_widget':
        vdomr_global['jp_invokable_functions'][callback_id] = callback

def _do_init():
    vdomr_global['mode']=_determine_mode()

    if vdomr_global['mode']=='colab':
        pass
    elif vdomr_global['mode']=='jp_proxy_widget':
        import jp_proxy_widget
        jp_widget = jp_proxy_widget.JSProxyWidget()
        jp_widget.element.html("<span id=jp_widget_empty></span>")
        jp_widget.js_init("""
        // Attach the callback to the global window object so
        // you can find it from anywhere:
        window.vdomr_invokeFunction = invokeFunction;
        """, invokeFunction=jp_proxy_widget_invokeFunction)
        vdomr_global['jp_widget']=jp_widget
        display(jp_widget)

def exec_javascript(js):
    if vdomr_global['mode']=='colab':
        from IPython.display import Javascript
        display(Javascript(js))
    elif vdomr_global['mode']=='jp_proxy_widget':
        vdomr_global['jp_widget'].js_init(js)
    else:
        from IPython.display import Javascript
        display(Javascript(js))

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

def _determine_mode():
    ## Note: this is tricky because we might be in a local runtime on colab.
    if os.environ.get('VDOMR_MODE','')=='JP_PROXY_WIDGET':
        print('vdomr: using jp_proxy_widget because of VDOMR_MODE environment variable')
        return 'jp_proxy_widget'
    if os.environ.get('VDOMR_MODE','')=='COLAB':
        print('vdomr: using colab because of VDOMR_MODE environment variable')
        return 'colab'
    if _found_jp_proxy_widget():
        if _found_colab():
            print('vdomr: unable to determine whether to use jp_proxy_widget or google colab')
            print('You should set the environment variable VDOMR_MODE to JP_PROXY_WIDGET or COLAB')
            return ''
        print('vdomr: using jp_proxy_widget')
        return 'jp_proxy_widget'
    if _found_colab():
        print('vdomr: using colab')
        return 'colab'
    print('vdomr: unable to import jp_proxy_widget or google.colab.colab_output')
    ## Note: this is tricky because we might be in a local runtime on colab.

_do_init()

