window.FeatureSpaceWidget=FeatureSpaceWidget;

PainterPath=window.PainterPath;
CanvasWidget=window.CanvasWidget;

// from https://gist.github.com/mucar/3898821
var colorArray = [
      '#FF6633', '#FFB399', '#FF33FF', '#FFFF99', '#00B3E6',
		  '#E6B333', '#3366E6', '#999966', '#99FF99', '#B34D4D',
		  '#80B300', '#809900', '#E6B3B3', '#6680B3', '#66991A',
		  '#FF99E6', '#CCFF1A', '#FF1A66', '#E6331A', '#33FFCC',
		  '#66994D', '#B366CC', '#4D8000', '#B33300', '#CC80CC',
		  '#66664D', '#991AFF', '#E666FF', '#4DB3FF', '#1AB399',
		  '#E666B3', '#33991A', '#CC9999', '#B3B31A', '#00E680',
		  '#4D8066', '#809980', '#E6FF80', '#1AFF33', '#999933',
		  '#FF3380', '#CCCC00', '#66E64D', '#4D80CC', '#9900B3',
      '#E64D66', '#4DB380', '#FF4D4D', '#99E6E6', '#6666FF'];

function FeatureSpaceWidget() {
    let that=this;

    this.setSize=function(W,H) {m_size=[W,H]; update_size();};
    this.element=function() {return m_div;};
    this.setTimeRange=function(t1,t2) {set_time_range(t1,t2);};
    this.translateTime=function(dt) {translate_time(dt);};
    this.zoomAmplitude=function(factor) {zoom_amplitude(factor);};
    this.setYOffsets=function(offsets) {m_y_offsets=clone(offsets); update_plot();};
    this.setYScaleFactor=function(factor) {m_y_scale_factor=factor; update_plot();};
    this.setFeatures=function(features) {m_features=features;};
    this.setFetX=function(fetx) { if(fetx == 'time') {m_fetx=0} else {m_fetx=fetx} };
    this.setFetY=function(fety) { if(fety == 'time') {m_fety=0} else {m_fety=fety} };
    this.clickStart=[0,0];
    this.clickEnd=[0,0];

    let m_div=$('<div tabindex="0" />'); // tabindex needed to handle keypress
    m_div.css({position:'absolute'});
    
    let menu_div = $('<div />')
      .append($('<input type="button" value="Zoom In"/>')
        .click(this.zoomAmplitude.bind(this,1/1.15))
      )
      .append($('<input type="button" value="Zoom Out"/>')
        .click(this.zoomAmplitude.bind(this,1.15))
      )
      .append($('<input type="button" value="Center on Circle"/>')
        .click(function () {
          console.log('m_',m_left,m_bottom);
          console.log('cl_',that.clickStart);
          m_left = m_left+(m_size[0]/2 - that.clickStart[0]);
          m_bottom = m_bottom+(m_size[1]/2 - that.clickStart[1]);
          that.clickStart = [m_size[0]/2, m_size[1]/2];
          console.log(m_left,m_bottom);
          update_plot();
        })
      )
      .append(
        $('<select id="fetx"><option value="0">Feature X</option></select>')
        .one('click', function () {
          $.each(['time',1,2,3,4,5,6], function(x,i) {
            let dropdown = $('#fetx').append($('<option></option>').val(x).html(i))
          })
        })
        .on('change', function () {that.setFetX(this.value);update_plot();})
      )
      .append(
        $('<select id="fety"><option value="1">Feature Y</option></select>')
        .one('click', function () {
          $.each(['time',1,2,3,4,5,6], function(x) {
            let dropdown = $('#fety').append($('<option></option>').val(x).html(x))
          })
        })
        .on('change', function () {that.setFetY(this.value);update_plot();})
      );
    m_div.append(menu_div)
    let m_size=[800,400];
    let m_main_canvas=new CanvasWidget();
    let m_main_f_canvas=new CanvasWidget();
    let m_cursor_canvas=new CanvasWidget();
    let m_trange=[0,1000];
    let m_current_time=-1;
    let m_y_scale_factor=1;
    let m_zoom_factor=1;
    let m_y_offsets=null;
    let m_margins={top:15,bottom:15,left:15,right:15};
    let m_mouse_handler=new MouseHandler(m_div);
    let m_mouse_press_anchor=null;
    let m_features=[[[],[]],[[],[]]]
    let m_fetx = 0;
    let m_fety = 1;
    let m_left = m_size[0]/2
    let m_bottom = m_size[1]/2
    let m_mouse_mode = 'cross';
    this.clickStart = [m_left,m_bottom];

    m_div.append(m_main_canvas.canvasElement());
    m_div.append(m_main_f_canvas.canvasElement());
    m_div.append(m_cursor_canvas.canvasElement());

    m_mouse_handler.onMousePress(handle_mouse_press);
    m_mouse_handler.onMouseRelease(handle_mouse_release);
    m_mouse_handler.onMouseMove(handle_mouse_move);
    m_mouse_handler.onMouseLeave(handle_mouse_leave);
    m_mouse_handler.onMouseWheel(handle_mouse_wheel);

    // Note that we cannot use this method within jupyter notebooks -- need to think about it
    m_div.bind('keydown',function(event) {
        console.log('keydown');
        switch(event.keyCode){
            case 38: handle_key_up(event); return false;
            case 40: handle_key_down(event); return false;
            case 37: handle_key_left(event); return false;
            case 39: handle_key_right(event); return false;
            default: console.info('key: '+event.keyCode);
        }
    });

    // computed in update_size:
    let m_time_axis_xrange=null;
    let m_channel_y_positions=null;
    let m_channel_spacing=null;

    m_main_canvas.onPaint(paint_main_canvas);
    m_main_f_canvas.onPaint(paint_main_f_canvas);
    m_cursor_canvas.onPaint(paint_cursor_canvas);

    function paint_main_canvas(painter) {
      painter.clear();
      let t1=Math.floor(m_trange[0]);
      let t2=Math.floor(m_trange[1]+1);
      if (t1<0) t1=0;
    }
    
    /*function get_abs_max(a) {
      return Math.max(Math.abs(...a.map(e => Array.isArray(e) ? get_abs_max(e) : e)));
    }

    function get_max(a) {
      return Math.max(...a.map(e => Array.isArray(e) ? get_max(e) : e));
    }*/

    function get_smallest_ind(a) {
      return a.reduce((iMax, x, i, arr) => x < arr[iMax] ? i : iMax, 0);
    }

    function paint_main_f_canvas(painter) {
        let f = m_features;
        let tol = 1 // Number of points we are happy to leave out in order to give extra space.
        let fx_max = Array(tol).fill(0);
        let fy_max = Array(tol).fill(0);
        let U = f.length

        for (let u=0; u < U; u++) {
          let fu = f[u];
          let fux = fu[m_fetx];
          let fuy = fu[m_fety];
          let n = fux.length;
          for (let i=0; i<n; i++) {
            if (fux[i] > Math.min(...fx_max)) {
              let smallest_ind = get_smallest_ind(fx_max);
              fx_max[smallest_ind] = fux[i];
            }
            if (fuy[i] > Math.min(...fy_max)) {
              let smallest_ind = get_smallest_ind(fy_max);
              fy_max[smallest_ind] = fuy[i];
            }
          }
        }
        let xlim = m_zoom_factor*(Math.min(...fx_max)/(m_size[0]/2));
        let ylim = m_zoom_factor*(Math.min(...fy_max)/(m_size[1]/2));

        painter.clear();
        for (let u=0; u < U; u++) {
          let fu = f[u];
          let fux = fu[m_fetx];
          let fuy = fu[m_fety];
          let n = fux.length;
          for (let i=0; i<n; i++) {
            let px = (fux[i]/xlim)+m_left; //(800-m_left);
            let py = (fuy[i]/ylim)+m_bottom; //(400-m_bottom);
            let rect = [px,py,2,2]
            painter.fillEllipse(rect,{'color':colorArray[u+4]})
          }
        }
    }

    function paint_cursor_canvas(painter) {
        painter.clear();
        let pt1=that.clickStart;
        console.log(pt1);
        if (m_mouse_mode == 'poly') {
          let pt2=that.clickEnd;
          painter.drawLine(pt1[0],pt1[1],pt2[0],pt2[1]);
        } else if (m_mouse_mode == 'cross') {
          let rect = [pt1[0], pt1[1], 10, 10];
          painter.drawEllipse(rect,{'color':'grey'})
        }
    }

    function zoom_amplitude(factor) {
        m_y_scale_factor*=factor;
        m_zoom_factor*=factor;
        update_plot();
    }

    function update_size() {
        m_main_canvas.setSize(m_size[0],m_size[1]);
        m_main_f_canvas.setSize(m_size[0],m_size[1]);
        m_cursor_canvas.setSize(m_size[0],m_size[1]);
        m_time_axis_xrange=[m_margins.left,m_size[0]-m_margins.right];
        m_div.css({width:m_size[0]+'px',height:m_size[1]+'px'})
        update_plot();
    }
    function update_plot() {
        update_cursor();
        m_main_canvas.update();
        m_main_f_canvas.update();
    }

    function update_cursor() {
        m_cursor_canvas.update();
    }

    function compute_mean(vals) {
        if (vals.length==0) return 0;
        let sum=0;
        for (let i in vals) sum+=vals[i];
        return sum/vals.length;
    }

    function handle_mouse_press(X) {
        if (m_mouse_mode == 'poly') {
        //console.log('press')
        if (!(m_mouse_press_anchor)) {
          m_mouse_press_anchor=clone(X);
        }
        m_mouse_press_anchor.trange=clone(m_trange);
        
        if(m_mouse_press_anchor.moving) {
          //console.log('done');
          m_mouse_press_anchor.moving = false;
          delete m_mouse_press_anchor
        } else {
          //console.log('start')
          that.clickStart=X.pos;
          m_mouse_press_anchor.moving = true;
        } } else if (m_mouse_mode == 'cross') {
          // Issue: currently mouse clicks are being handled even on button press which is undesirable.
          // For now we take advantage of the fact the buttons are at the top, but need to think about it.
          if (X.pos[1] > 35) { // TODO: Find a less hacky way to fix this.
            that.clickStart=X.pos;
            update_cursor();
          }
        }
    }

    function handle_mouse_release(X) {
      //console.log('release');
        that.clickEnd=X.pos
    }

    function handle_mouse_leave(X) {
        //console.log('leave')
        //m_mouse_press_anchor=null;
    }

    function handle_mouse_move(X) {
      //console.log('moving')
      if (m_mouse_mode == 'poly') {
        if (m_mouse_press_anchor) {
          if (m_mouse_press_anchor.moving) {
            that.clickEnd=X.pos;
            update_cursor();
            m_mouse_press_anchor.moving=true;
            //console.log('moving with anchor')
          }
        }
      }
      return 0
    }

    function handle_key_up(X) {
        that.zoomAmplitude(1.15);
    }
    function handle_key_down(X) {
        that.zoomAmplitude(1/1.15);
    }
    function handle_key_left(X) {
        let span=m_trange[1]-m_trange[0];
        that.translateTime(-span*0.2);
    }
    function handle_key_right(X) {
        let span=m_trange[1]-m_trange[0];
        that.translateTime(span*0.2);
    }

    function handle_mouse_wheel(X) {
      // wheel
    }

    update_size();
}


function MouseHandler(elmt) {
    this.onMousePress=function(handler) {m_handlers['press'].push(handler);};
    this.onMouseRelease=function(handler) {m_handlers['release'].push(handler);};
    this.onMouseMove=function(handler) {m_handlers['move'].push(handler);};
    this.onMouseEnter=function(handler) {m_handlers['enter'].push(handler);};
    this.onMouseLeave=function(handler) {m_handlers['leave'].push(handler);};
    this.onMouseWheel=function(handler) {m_handlers['wheel'].push(handler);};

    elmt.mousedown(function(e) {report('press',mouse_event($(this),e)); return true;});
    elmt.mouseup(function(e) {report('release',mouse_event($(this),e)); return true;});
    elmt.mousemove(function(e) {report('move',mouse_event($(this),e)); return true;});
    elmt.mouseenter(function(e) {report('enter',mouse_event($(this),e)); return true;});
    elmt.mouseleave(function(e) {report('leave',mouse_event($(this),e)); return true;});
    elmt.on('dragstart',function() {return false;});
    elmt.on('mousewheel', function(e){report('wheel',wheel_event($(this),e)); return false;});

    let m_handlers={
        press:[],release:[],move:[],enter:[],leave:[],wheel:[]
    };

    function report(name,X) {
        for (i in m_handlers[name]) {
            m_handlers[name][i](X);
        }
    }

    function mouse_event(elmt,e) {
        //var parentOffset = $(this).parent().offset(); 
        var offset=elmt.offset(); //if you really just want the current element's offset
        var posx = e.pageX - offset.left;
        var posy = e.pageY - offset.top;
        return {
            pos:[posx,posy],
            modifiers:{ctrlKey:e.ctrlKey}
        };
    }
    function wheel_event(elmt,e) {
        return {
            delta:e.originalEvent.wheelDelta
        };
    }

}

function clone(obj) {
    return JSON.parse(JSON.stringify(obj));
}

// Standard Normal variate using Box-Muller transform.
function randn_bm() {
    var u = 0, v = 0;
    while(u === 0) u = Math.random(); //Converting [0,1) to (0,1)
    while(v === 0) v = Math.random();
    return Math.sqrt( -2.0 * Math.log( u ) ) * Math.cos( 2.0 * Math.PI * v );
}

