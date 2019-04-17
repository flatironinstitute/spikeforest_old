import time

import random
import string
import traceback

import json

import os
import vdomr as vd
from .vdomr import _get_init_javascript


class VDOMRServer():
    def __init__(self, vdomr_app):
        self._vdomr_app = vdomr_app
        self._sessions = dict()
        self._port = None
        self._token = os.environ.get('VDOMR_TOKEN', _random_string(10))

    def setPort(self, port):
        self._port = port

    def setToken(self, token):
        self._token = token

    def start(self):
        try:
            import tornado.httpserver
            import tornado.ioloop
            import tornado.options
            import tornado.web

            from tornado.ioloop import IOLoop
            from tornado import gen
        except:
            raise Exception(
                'Problem importing tornado. Try "pip install tornado".')

        server_self = self

        class RootHandler(tornado.web.RequestHandler):
            def get(self):
                session_id = ''.join(random.choices(
                    string.ascii_uppercase + string.digits, k=10))
                server_self._sessions[session_id] = dict(
                    root=None
                )
                vd._set_server_session(session_id)

                root = server_self._vdomr_app.createSession()
                server_self._sessions[session_id]['root'] = root

                html = '''
                <head>
                <script>
                    function post_json(url,obj,callback) {
                    xhr = new XMLHttpRequest();
                    xhr.open("POST", url, true);
                    xhr.setRequestHeader("Content-type", "application/json");
                    xhr.onreadystatechange = function () {
                        if (xhr.readyState == 4 && xhr.status == 200) {
                            var resp;
                            try {
                                resp=JSON.parse(xhr.responseText);
                            }
                            catch(err) {
                                callback('Problem parsing json response.');
                                return;
                            }
                            if (resp.success) {
                                callback(null,resp);
                            }
                            else {
                                callback('Error: '+resp.error);
                            }
                        }
                    }
                    var data = JSON.stringify(obj);
                    xhr.send(data);
                    }
                    function inject_script(url,callback) {
                        var head = document.getElementsByTagName('head')[0];
                        var script = document.createElement('script');
                        script.type = 'text/javascript';
                        script.onload = function() {
                            callback();
                        }
                        script.src = url;
                        head.appendChild(script);
                    }
                </script>

                <script>
                window.vdomr_invokeFunction=function(callback_id,args,kwargs) {
                    // console.log('vdomr_invokeFunction',callback_id,args,kwargs);
                    // document.getElementById('overlay').style.visibility='visible'
                    post_json('/{vdomr_token_str}invoke/?session_id={session_id}',{callback_id:callback_id,args:args,kwargs:kwargs},function(err,resp) {
                    // document.getElementById('overlay').style.visibility='hidden'
                    if (err) {
                        console.error(err);
                        return;
                    }
                    // console.log('ok',resp);
                    inject_script('/{vdomr_token_str}script_immediate.js?session_id={session_id}',function() {

                    });
                    });
                }
                {init_js}
                </script>

                <script>
                    function get_script() {
                        inject_script('/{vdomr_token_str}script.js?session_id={session_id}',function() {
                            setTimeout(function() {
                                get_script();
                            },0);
                        });
                    }
                    setTimeout(function() {
                        get_script();
                    },100);
                </script>

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
                <html>
                <div id=overlay class=overlay style="visibility:hidden">Please wait...</div>
                {content}
                </html>
                '''
                html = root._repr_html_().join(html.split('{content}'))
                html = session_id.join(html.split('{session_id}'))
                html = html.replace('{init_js}', _get_init_javascript())
                if server_self._token:
                    html = html.replace('{vdomr_token_str}', server_self._token+'/')
                else:
                    html = html.replace('{vdomr_token_str}', '')
                self.write(html)

        class InvokeHandler(tornado.web.RequestHandler):
            def post(self):
                session_id = self.get_argument('session_id', None)
                if not session_id:
                    self.write(dict(success=False, error='No session_id'))
                    return
                vd._set_server_session(session_id)
                try:
                    data = json.loads(self.request.body)
                except:
                    self.write(
                        dict(success=False, error='Missing self.request.body'))
                    return
                try:
                    obj = json.loads(self.request.body)
                except:
                    self.write(
                        dict(success=False, error='Unable to parse body'))
                    return
                if 'callback_id' not in obj:
                    self.write(
                        dict(success=False, error='Missing callback_id'))
                    return
                callback_id = obj['callback_id']
                args = obj['args']
                kwargs = obj['kwargs']
                try:
                    retval = vd.invoke_callback(
                        callback_id, argument_list=args, kwargs=kwargs)
                except:
                    traceback.print_exc()
                    self.write(
                        dict(success=False, error='Error invoking callback.'))
                    return
                self.write(dict(success=True, retval=retval))

        @gen.coroutine
        def async_sleep(seconds):
            yield gen.Task(IOLoop.instance().add_timeout, time.time() + seconds)

        class ScriptHandler(tornado.web.RequestHandler):
            @gen.coroutine
            def get(self):
                session_id = self.get_argument('session_id', None)
                if not session_id:
                    self.write('//no session_id')
                    return
                delay = 1
                num_delays = 10
                for i in range(num_delays):
                    vd._set_server_session(session_id)
                    js_list = []
                    while True:
                        js = vd._take_javascript_to_execute()
                        if js is None:
                            break
                        js_list.append(js)
                    if len(js_list) > 0:
                        self.write('\n\n'.join(js_list))
                        break
                    yield async_sleep(delay)
                self.write("(function() {/*nothing to do*/})")

        class ScriptImmediateHandler(tornado.web.RequestHandler):
            @gen.coroutine
            def get(self):
                session_id = self.get_argument('session_id', None)
                if not session_id:
                    self.write('//no session_id')
                    return
                vd._set_server_session(session_id)
                js_list = []
                while True:
                    js = vd._take_javascript_to_execute()
                    if js is None:
                        break
                    js_list.append(js)
                if len(js_list) > 0:
                    self.write('\n\n'.join(js_list))
                else:
                    self.write('(function() {/*nothing to do --*/})')

        if self._port is not None:
            port = self._port
        else:
            port = os.environ.get('PORT', 3005)


        _root_path='/'
        _invoke_path='/invoke/'
        _script_path='/script.js'
        _script_immediate_path='/script_immediate.js'

        if self._token:
            _root_path='/{}{}'.format(self._token, _root_path)
            _invoke_path='/{}{}'.format(self._token, _invoke_path)
            _script_path='/{}{}'.format(self._token, _script_path)
            _script_immediate_path='/{}{}'.format(self._token, _script_immediate_path)

        application = tornado.web.Application([
            (_root_path, RootHandler),
            (_invoke_path, InvokeHandler),
            (_script_path, ScriptHandler),
            (_script_immediate_path, ScriptImmediateHandler)
        ])
        http_server = tornado.httpserver.HTTPServer(application)
        http_server.listen(port)
        if self._token:
            print('VDOMR server is listening on port {} with token {}'.format(port, self._token))
            print('http://localhost:{}/{}/'.format(port, self._token))
        else:
            print('VDOMR server is listening on port {}'.format(port))
            print('http://localhost:{}'.format(port))
        tornado.ioloop.IOLoop.current().start()

def _random_string(num):
    return ''.join(random.choices('abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ', k=num))