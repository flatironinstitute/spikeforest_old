window.TemplateWidget=TemplateWidget;

PainterPath=window.PainterPath;
CanvasWidget=window.CanvasWidget;

function TemplateWidget() {
    let that=this;

    this.setTemplate=function(X) {setTemplate(X);};
    this.setSize=function(W,H) {m_size=[W,H]; update_size();};
    this.element=function() {return m_div;};
    this.zoomAmplitude=function(factor) {zoom_amplitude(factor);};
    this.setYOffsets=function(offsets) {m_y_offsets=clone(offsets); update_plot();};
    this.setYScaleFactor=function(factor) {m_y_scale_factor=factor; update_plot();};

    let m_div=$('<div tabindex="0" />'); // tabindex needed to handle keypress
    m_div.css({position:'absolute'});
    let m_size=[200,200];
    let m_template=null;
    let m_main_canvas=new CanvasWidget();
    let m_y_scale_factor=null;
    let m_default_y_scale_factor=1;
    let m_y_offsets=null;
    let m_margins={top:15,bottom:15,left:15,right:15};
    let m_mouse_handler=new MouseHandler(m_div);

    m_div.append(m_main_canvas.canvasElement());

    m_mouse_handler.onMousePress(handle_mouse_press);
    m_mouse_handler.onMouseRelease(handle_mouse_release);
    m_mouse_handler.onMouseMove(handle_mouse_move);
    m_mouse_handler.onMouseLeave(handle_mouse_leave);
    //m_mouse_handler.onMouseWheel(handle_mouse_wheel);

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

    // computed in update_size:
    let m_time_axis_xrange=null;
    let m_channel_y_positions=null;
    let m_channel_spacing=null;
    let m_channel_colors=mv_default_channel_colors();

    m_main_canvas.onPaint(paint_main_canvas);

    function paint_main_canvas(painter) {
        painter.clear();
        if (!m_template) return;
        let M=m_template.N1(); // number of channels
        let T=m_template.N2(); // number of timepoints
        for (let m=0; m<M; m++) {
            painter.setPen({'color':m_channel_colors[m % m_channel_colors.length]});
            let pp=new PainterPath();
            for (let tt=0; tt<T; tt++) {
                let val=m_template.value(m, tt);
                if (!isNaN(val)) {
                    let pt=val2pix(m,tt,val);
                    pp.lineTo(pt[0],pt[1]);
                }
                else {
                    let pt=val2pix(m,tt,0);
                    pp.moveTo(pt[0],pt[1]);
                }
            }
            painter.drawPath(pp);
        }
    }

    function zoom_amplitude(factor) {
        if (m_y_scale_factor) m_y_scale_factor*=factor;
        m_default_y_scale_factor*=factor;
        update_plot();
    }

    function val2pix(ch,t,val) {
        if (m_template) T = m_template.N2();
        else T = 1;
        let y_scale_factor = m_y_scale_factor||m_default_y_scale_factor;
        let y0=m_channel_y_positions[ch];
        y0-=(val+m_y_offsets[ch])*y_scale_factor*m_channel_spacing/2;
        let xpct=t/T;
        let x0=m_time_axis_xrange[0]+(m_time_axis_xrange[1]-m_time_axis_xrange[0])*xpct;
        return [x0,y0];
    }

    function pix2time(pix) {
        if (m_template) T = m_template.N2();
        else T = 1;
        let xpct=(pix[0]-m_time_axis_xrange[0])/(m_time_axis_xrange[1]-m_time_axis_xrange[0]);
        let t=xpct*T;
        return t;
    }

    function update_size() {
        m_main_canvas.setSize(m_size[0],m_size[1]);
        m_time_axis_xrange=[m_margins.left,m_size[0]-m_margins.right];
        m_div.css({width:m_size[0]+'px',height:m_size[1]+'px'});
        update_plot();
    }
    function update_plot() {
        let timer=new Date();
        if (!m_template) return;
        let M=m_template.N1(); // number of channels
        let T=m_template.N2(); // number of timepoints

        let H0=m_size[1]-m_margins.top-m_margins.bottom;;
        m_channel_spacing=H0/M;
        m_channel_y_positions=[];
        let y0=m_size[1]-m_margins.bottom-m_channel_spacing/2;
        for (let m=0; m<M; m++) {
            m_channel_y_positions.push(y0);
            y0-=m_channel_spacing;
        }

        m_main_canvas.update();
    }

    function compute_mean(vals) {
        let sum=0;
        let count=0;
        for (let i in vals) {
            if (!isNaN(vals[i])) {
                sum+=vals[i];
                count++;
            }
        }
        if (!count) return 0;
        return sum/count;
    }

    function setTemplate(X) {
        m_template=X;
        auto_compute_y_offsets();
        auto_compute_default_y_scale_factor();
    }

    function auto_compute_y_offsets() {
        if (!m_template) return;
        let M=m_template.N1(); // number of channels
        let T=m_template.N2(); // number of timepoints

        let offsets=[];
        for (let m=0; m<M; m++) {
            /*let data=[];
            for (let t=0; t<T; t++) {
                data.push(m_template.value(m,t));
            }
            let mean0=compute_mean(data);
            offsets.push(-mean0);
            */
           //actually for now the offsets are going to be all zero
           offsets.push(0)
        }
        that.setYOffsets(offsets);
    }

    function auto_compute_default_y_scale_factor() {
        let vals=[];
        let M=m_template.N1(); // number of channels
        let T=m_template.N2(); // number of timepoints
        for (let m=0; m<M; m++) {
            let data=[];
            for (let t=0; t<T; t++) {
                data.push(m_template.value(m,t));
            }
            for (let j in data) {
                if (!isNaN(data[j])) {
                    vals.push(Math.abs(data[j]+m_y_offsets[m]));
                }
            }
        }
        if (vals.length > 0) {
            vals.sort(function(a, b){return a - b});
            let vv=vals[Math.floor(vals.length*0.9)];
            if (vv>0)
                m_default_y_scale_factor=(1/(2*vv));
            else
                m_default_y_scale_factor=1;
            update_plot();
        }
    }

    function handle_mouse_press(X) {
    }

    function handle_mouse_release(X) {
    }

    function handle_mouse_leave(X) {
    }

    function handle_mouse_move(X) {
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

    let dummy=new window.Mda(0,0);
    that.setTemplate(dummy);
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
    //elmt.on('mousewheel', function(e){report('wheel',wheel_event($(this),e)); return false;});

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
