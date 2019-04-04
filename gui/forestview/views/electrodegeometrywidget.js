window.ElectrodeGeometryWidget=ElectrodeGeometryWidget;

PainterPath=window.PainterPath;
CanvasWidget=window.CanvasWidget;

function ElectrodeGeometryWidget() {
    let that=this;

    this.setElectrodeLocations=function(locations) {setElectrodeLocations(locations);};
    this.setElectrodeLabels=function(labels) {setElectrodeLabels(labels);};
    this.setCurrentElectrodeIndex=function(ind) {setCurrentElectrodeIndex(ind);};
    this.currentElectrodeIndex=function() {return m_current_electrode_index;};
    this.onCurrentElectrodeIndexChanged=function(handler) {m_current_electrode_index_changed_handlers.push(handler);};
    this.setSize=function(W,H) {m_size=[W,H]; update_size();};
    this.element=function() {return m_div;};

    let m_div=$('<div tabindex="0" />'); // tabindex needed to handle keypress
    m_div.css({position:'absolute'});
    let m_size=[200,200];
    let m_locations=null;
    let m_labels=[];
    let m_xmin = 0, m_xmax = 1;
    let m_ymin = 0, m_ymax = 1;
    let m_mindist = 0;
    let m_transpose = false;
    let m_main_canvas=new CanvasWidget();
    let m_margins={top:15,bottom:15,left:15,right:15};
    let m_mouse_handler=new MouseHandler(m_div);
    let m_channel_rects={};
    let m_hovered_electrode_index=-1;
    let m_current_electrode_index=-1;
    let m_current_electrode_index_changed_handlers=[];

    m_div.append(m_main_canvas.canvasElement());

    m_mouse_handler.onMousePress(handle_mouse_press);
    m_mouse_handler.onMouseRelease(handle_mouse_release);
    m_mouse_handler.onMouseMove(handle_mouse_move);
    m_mouse_handler.onMouseLeave(handle_mouse_leave);
    m_mouse_handler.onMouseWheel(handle_mouse_wheel);

    // Note that we cannot use this method within jupyter notebooks -- need to think about it
    m_div.bind('keydown',function(event) {
        switch(event.keyCode){
            case 38: handle_key_up(event); return false;
            case 40: handle_key_down(event); return false;
            case 37: handle_key_left(event); return false;
            case 39: handle_key_right(event); return false;
            default: console.info('key: '+event.keyCode);
        }
    });

    m_main_canvas.onPaint(paint_main_canvas);

    function paint_main_canvas(painter) {
        painter.clear();
        let W=m_size[0];
        let H=m_size[1];
        
        let W1 = W, H1 = H;
        if (m_transpose) {
            W1 = H;
            H1 = W;
        }

        let x1 = m_xmin - m_mindist, x2 = m_xmax + m_mindist;
        let y1 = m_ymin - m_mindist, y2 = m_ymax + m_mindist;
        let w0 = x2 - x1, h0 = y2 - y1;
        let offset, scale;
        if (w0 * H1 > h0 * W1) {
            scale = W1 / w0;
            offset = [0 - x1 * scale, (H1 - h0 * scale) / 2 - y1 * scale];
        } else {
            scale = H1 / h0;
            offset = [(W1 - w0 * scale) / 2 - x1 * scale, 0 - y1 * scale];
        }
        m_channel_rects=[];
        for (let i in m_locations) {
            let pt0 = m_locations[i];
            let x = pt0[0] * scale + offset[0];
            let y = pt0[1] * scale + offset[1];
            let rad = m_mindist * scale / 3;
            let x1 = x, y1 = y;
            if (m_transpose) {
                x1 = y;
                y1 = x;
            }
            let col = get_channel_color(i);
            let rect0 = [x1 - rad, y1 - rad, rad * 2, rad * 2];
            painter.fillEllipse(rect0, col);
            m_channel_rects[i] = rect0;
            let label0 = m_labels[i];
            if ((label0) || (label0==0)) {
                painter.setBrush({color:'white'});
                painter.setFont({'pixel-size':rad});
                painter.drawText(rect0, {AlignCenter: true, AlignVCenter: true}, label0);
            }
        }
    }

    function update_size() {
        m_main_canvas.setSize(m_size[0],m_size[1]);
        m_div.css({width:m_size[0]+'px',height:m_size[1]+'px'});
        update_positions();
    }
    function update_positions() {
        let pt0 = m_locations[0] || [0, 0];
        let xmin = pt0[0], xmax = pt0[0];
        let ymin = pt0[1], ymax = pt0[1];
        for (let i in m_locations) {
            let pt = m_locations[i];
            xmin = Math.min(xmin, pt[0]);
            xmax = Math.max(xmax, pt[0]);
            ymin = Math.min(ymin, pt[1]);
            ymax = Math.max(ymax, pt[1]);
        }
        if (xmax == xmin) xmax++;
        if (ymax == ymin) ymax++;

        m_xmin = xmin; m_xmax = xmax;
        m_ymin = ymin; m_ymax = ymax;

        m_transpose = (m_ymax - m_ymin > m_xmax - m_xmin);

        let mindists = [];
        for (var i in m_locations) {
            let pt0 = m_locations[i];
            let mindist = -1;
            for (let j in m_locations) {
                let pt1 = m_locations[j];
                let dx = pt1[0] - pt0[0];
                let dy = pt1[1] - pt0[1];
                let dist = Math.sqrt(dx * dx + dy * dy);
                if (dist > 0) {
                    if ((dist < mindist) || (mindist < 0))
                        mindist = dist;
                    }
                }
            if (mindist > 0) mindists.push(mindist);
        }
        let avg_mindist = compute_average(mindists);
        if (avg_mindist <= 0) avg_mindist = 1;
            m_mindist = avg_mindist;
        
        m_main_canvas.update();
    }

    function compute_average(list) {
        if (list.length == 0) return 0;
        var sum = 0;
        for (var i in list) sum += list[i];
        return sum / list.length;
      }

    function setElectrodeLocations(locations) {
        m_locations=locations;
        update_positions();
    }
    function setElectrodeLabels(labels) {
        m_labels=labels;
        m_main_canvas.update();
    }
    function setCurrentElectrodeIndex(ind) {
        set_current_electrode_index(ind);
    }

    function elec_index_at_pixel(pos) {
        for (let i in m_channel_rects) {
            rect0 = m_channel_rects[i];
            if ((rect0[0]<=pos[0])&&(pos[0]<=rect0[0]+rect0[2])) {
                if ((rect0[1]<=pos[1])&&(pos[1]<=rect0[1]+rect0[2])) {
                    return i;
                }
            }
        }
        return -1;
    }

    function set_hovered_electrode_index(ind) {
        if (ind == m_hovered_electrode_index) return;
        m_hovered_electrode_index=ind;
        m_main_canvas.update();
    }

    function set_current_electrode_index(ind) {
        if (ind == m_current_electrode_index) return;
        m_current_electrode_index=ind;
        m_main_canvas.update();
        m_current_electrode_index_changed_handlers.forEach(function(handler) {
            handler();
        });
    }

    function get_channel_color(ind) {
        let color='rgb(0,0,255)';
        let color_hover='rgb(100,100,255)';
        let color_current='rgb(200,200,100)';
        let color_current_hover='rgb(220,220,150)';

        if (ind == m_current_electrode_index) {
            if (ind == m_hovered_electrode_index) return color_current_hover;
            else return color_current;
        }
        else {
            if (ind == m_hovered_electrode_index) return color_hover;
            else return color;
        }
    }

    function handle_mouse_press(X) {
    }

    function handle_mouse_release(X) {
        let elec_ind = elec_index_at_pixel(X.pos);
        set_current_electrode_index(elec_ind);
    }

    function handle_mouse_leave(X) {
        set_hovered_electrode_index(-1);
    }

    function handle_mouse_move(X) {
        let elec_ind = elec_index_at_pixel(X.pos);
        set_hovered_electrode_index(elec_ind);
    }

    function handle_key_up(X) {
        that.zoomAmplitude(1.15);
    }
    function handle_key_down(X) {
        that.zoomAmplitude(1/1.15);
    }
    function handle_key_left(X) {
    }
    function handle_key_right(X) {
    }

    function handle_mouse_wheel(X) {
    }

    let dummy=[];
    that.setElectrodeLocations(dummy);
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

function mv_default_channel_colors() {
    var ret=[];
    ret.push('rgb(40,40,40)');
    ret.push('rgb(64,32,32)');
    ret.push('rgb(32,64,32)');
    ret.push('rgb(32,32,112)');
    return ret;
}
