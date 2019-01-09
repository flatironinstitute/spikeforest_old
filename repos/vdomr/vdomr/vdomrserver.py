import time

import random
import string
import traceback
import uuid

import json

import os
import vdomr as vd

class VDOMRServer():
  def __init__(self,vdomr_app):
    self._vdomr_app=vdomr_app
    pass
  def start(self):
    _start_vdomr_server(self._vdomr_app)

def _start_vdomr_server(vdomr_app):
  try:
    import tornado.httpserver
    import tornado.ioloop
    import tornado.options
    import tornado.web

    from tornado.ioloop import IOLoop
    from tornado import gen 
  except:
    raise Exception('Problem importing tornado. Try "pip install tornado".')

  if os.environ.get('VDOMR_MODE',None)!='SERVER':
    raise Exception('You must set the environment variable VDOMR_MODE to "SERVER"')


  sessions=dict()
  class RootHandler(tornado.web.RequestHandler):
      def get(self):
        session_id=''.join(random.choices(string.ascii_uppercase + string.digits, k=10))
        sessions[session_id]=dict(
          root=None
        )
        vd._set_server_session(session_id)

        root=vdomr_app.createSession()
        sessions[session_id]['root']=root

        
        html='''
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
            console.log('vdomr_invokeFunction',callback_id,args,kwargs);
            document.getElementById('overlay').style.visibility='visible'
            post_json('/invoke/?session_id={session_id}',{callback_id:callback_id,args:args,kwargs:kwargs},function(err,resp) {
            document.getElementById('overlay').style.visibility='hidden'
              if (err) {
                console.error(err);
                return;
              }
              console.log('ok',resp);
              inject_script('/script_immediate.js?session_id={session_id}',function() {

              });
            });
          }
          </script>

          <script>
            function get_script() {
              inject_script('/script.js?session_id={session_id}',function() {
                setTimeout(function() {
                  get_script();
                },100);
              });
            }
            setTimeout(function() {
              get_script();
            },1000);
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
        html=root._repr_html_().join(html.split('{content}'))
        html=session_id.join(html.split('{session_id}'))
        self.write(html)
        
  class InvokeHandler(tornado.web.RequestHandler):
      def post(self):
        session_id=self.get_argument('session_id',None)
        if not session_id:
          self.write(dict(success=False,error='No session_id'))
          return
        vd._set_server_session(session_id)
        try:
          data = json.loads(self.request.body)
        except:
          self.write(dict(success=False,error='Missing self.request.body'))
          return
        try:
          obj=json.loads(self.request.body)
        except:
          self.write(dict(success=False,error='Unable to parse body'))
          return
        if 'callback_id' not in obj:
          self.write(dict(success=False,error='Missing callback_id'))
          return
        callback_id=obj['callback_id']
        args=obj['args']
        kwargs=obj['kwargs']
        try:
          retval=vd.invoke_callback(callback_id,argument_list=args,kwargs=kwargs)
        except:
          traceback.print_exc()
          self.write(dict(success=False,error='Error invoking callback.'))
          return
        self.write(dict(success=True,retval=retval))

  @gen.coroutine
  def async_sleep(seconds):
      yield gen.Task(IOLoop.instance().add_timeout, time.time() + seconds)

  class ScriptHandler(tornado.web.RequestHandler):
      @gen.coroutine
      def get(self):
        session_id=self.get_argument('session_id',None)
        if not session_id:
          self.write('//no session_id')
          return
        delay=1
        num_delays=10
        for i in range(num_delays):
          vd._set_server_session(session_id)
          js=vd._take_javascript_to_execute()
          if js:
            self.write(js)
            return
          yield async_sleep(delay)
        self.write("//nothing to do")

  class ScriptImmediateHandler(tornado.web.RequestHandler):
      @gen.coroutine
      def get(self):
        session_id=self.get_argument('session_id',None)
        if not session_id:
          self.write('//no session_id')
          return
        vd._set_server_session(session_id)
        js=vd._take_javascript_to_execute()
        if js:
          self.write(js)
        else:
          self.write('//nothing to do')

  port=os.environ.get('PORT',3005)
  application = tornado.web.Application([
    (r"/", RootHandler),
    (r"/invoke/", InvokeHandler),
    (r"/script.js", ScriptHandler),
    (r"/script_immediate.js", ScriptImmediateHandler)
  ])
  http_server = tornado.httpserver.HTTPServer(application)
  http_server.listen(port)
  print('VDOMR server is listening on port {}'.format(port))
  tornado.ioloop.IOLoop.current().start()