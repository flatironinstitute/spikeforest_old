window.TimeseriesWidget=TimeseriesWidget;

PainterPath=window.PainterPath;
CanvasWidget=window.CanvasWidget;

window.timeserieswidget_sync_groups = window.timeserieswidget_sync_groups||{};

function TimeseriesWidget() {
    let that=this;

    this.setTimeseriesModel=function(M) {setTimeseriesModel(M);};
    this.setSize=function(W,H) {m_size=[W,H]; update_size();};
    this.element=function() {return m_div;};
    this.setTimeRange=function(t1,t2) {set_time_range(t1,t2);};
    this.timeRange=function() {return clone(m_trange);};
    this.onTimeRangeChanged=function(handler) {m_div.on('time-range-changed', handler);};
    this.setCurrentTime=function(t) {set_current_time(t);};
    this.currentTime=function() {return m_current_time;};
    this.onCurrentTimeChanged=function(handler) {m_div.on('current-time-changed', handler);};
    this.zoomTime=function(factor) {zoom_time(factor);};
    this.translateTime=function(dt) {translate_time(dt);};
    this.zoomAmplitude=function(factor) {zoom_amplitude(factor);};
    this.setYOffsets=function(offsets) {m_y_offsets=clone(offsets); update_plot();};
    this.setYScaleFactor=function(factor) {m_y_scale_factor=factor; update_plot();};
    this.setMarkers=function(markers) { m_markers=markers;};
    this.setSyncGroup=function(sync_group_name) {setSyncGroup(sync_group_name);};
    this.autoScale=function() {auto_scale();};
    this._triggerOff=function() {m_do_trigger=false;};
    this._triggerOn=function() {m_do_trigger=true;};

    let m_div=$('<div tabindex="0" />'); // tabindex needed to handle keypress
    m_div.css({position:'absolute'});
    let m_size=[800,500];
    let m_model=null;
    let m_main_canvas=new CanvasWidget();
    let m_cursor_canvas=new CanvasWidget();
    let m_trange=[0,5000];
    let m_current_time=-1;
    let m_y_scale_factor=1;
    let m_y_offsets=null;
    let m_margins={top:15,bottom:15,left:15,right:15};
    let m_mouse_handler=new MouseHandler(m_div);
    let m_mouse_press_anchor=null;
    // let m_markers=[[100,1000],[150,1050]];
    let m_markers=[];
    let m_do_trigger=true;

    m_div.append(m_main_canvas.canvasElement());
    m_div.append(m_cursor_canvas.canvasElement());

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
            case 187: that.zoomTime(1.15); return false;
            case 189: that.zoomTime(1/1.15); return false;
            default: console.info('key: '+event.keyCode);
        }
    });

    // computed in update_size:
    let m_time_axis_xrange=null;
    let m_channel_y_positions=null;
    let m_channel_spacing=null;
    let m_channel_colors=mv_default_channel_colors();

    m_main_canvas.onPaint(paint_main_canvas);
    m_cursor_canvas.onPaint(paint_cursor_canvas);

    function determine_downsample_factor_from_num_timepoints(target_num_pix, num) {
        let ds_factor = 1;
        let factor = 3;
        while (num/(ds_factor*factor) > target_num_pix) {
            ds_factor*=factor;
        }
        return ds_factor;
    }

    function paint_main_canvas(painter) {
        painter.clear();
        let M=m_model.numChannels();
        let t1=Math.floor(m_trange[0]);
        let t2=Math.floor(m_trange[1]+1);
        if (t1<0) t1=0;
        if (t2>=m_model.numTimepoints()) t2=m_model.numTimepoints();
        let downsample_factor = determine_downsample_factor_from_num_timepoints(m_size[0]*1.3, t2-t1);
        let t1b = Math.floor(t1/downsample_factor);
        let t2b = Math.floor(t2/downsample_factor);
        for (let m=0; m<M; m++) {
            painter.setPen({'color':m_channel_colors[m % m_channel_colors.length]});
            let pp=new PainterPath();
            let data0=m_model.getChannelData(m, t1b, t2b, downsample_factor);
            // trigger pre-loading
            m_model.getChannelData(m, Math.floor(t1b/3), Math.floor(t2b/3), downsample_factor*3, {request_only:true});
            if ((downsample_factor>1) && (m_current_time>=0)) {
                t1c = Math.floor(Math.max(0, (m_current_time-800)/(downsample_factor/3)))
                t2c = Math.floor(Math.min(m_model.numTimepoints(), (m_current_time+800)/(downsample_factor/3)))
                m_model.getChannelData(m, t1c, t2c, downsample_factor/3, {request_only:true});
            }
            if (downsample_factor == 1) {
                for (let tt=t1; tt<t2; tt++) {
                    let val=data0[tt-t1];
                    if (!isNaN(val)) {
                        let pt=val2pix(m,tt,val);
                        pp.lineTo(pt[0],pt[1]);
                    }
                    else {
                        let pt=val2pix(m,tt,0);
                        pp.moveTo(pt[0],pt[1]);
                    }
                }
            }
            else {
                for (let tt=t1b; tt<t2b; tt++) {
                    let val_min=data0[(tt-t1b)*2];
                    let val_max=data0[(tt-t1b)*2+1];
                    if ((!isNaN(val_min))&&(!isNaN(val_max))) {
                        let pt_min=val2pix(m,tt*downsample_factor,val_min);
                        let pt_max=val2pix(m,tt*downsample_factor,val_max);
                        pp.lineTo(pt_min[0],pt_min[1]);
                        pp.lineTo(pt_max[0],pt_max[1]);
                    }
                    else {
                        let pt=val2pix(m,tt*downsample_factor,0);
                        pp.moveTo(pt[0],pt[1]);
                    }
                }
            }
            painter.drawPath(pp);
        }
    }

    function paint_cursor_canvas(painter) {
        painter.clear();
        let M=m_model.numChannels();
        let pt1=val2pix(M-1,m_current_time,-m_y_offsets[M-1]);
        let pt2=val2pix(0,m_current_time,-m_y_offsets[0]);
        painter.drawLine(pt1[0],pt1[1]-m_channel_spacing/2,pt2[0],pt2[1]+m_channel_spacing/2);
        add_markers(painter)
    }

    function add_markers(painter) {
        painter.setFont({"pixel-size":18,family:'Arial'});

        let M=m_model.numChannels();
        let i = 0
        for (m_marker_group of m_markers) {
          i = i + 1;
          // col = colorArray[i % colorArray.length]
          col = 'red'
          painter.setPen({'color':col});
          painter.setBrush({'color':col});
          for(m of m_marker_group) {
            let pt1=val2pix(M-1,m,-m_y_offsets[M-1]);
            let pt2=val2pix(0,m,-m_y_offsets[0]);
            let rect = [pt1[0],pt1[1]-m_channel_spacing/2,pt2[0],pt2[1]+m_channel_spacing/2]
            painter.drawLine(...rect);
            rect[0] = rect[0] + 5;
            painter.drawText(rect, {AlignLeft: true, AlignTop: true}, ""+i);
          }
        }
    }

    function set_time_range(t1,t2) {
        let N=m_model.numTimepoints();
        if (t2>N) {t1-=(t2-N); t2-=(t2-N);};
        if (t1<=0) {t2-=t1; t1-=t1;};
        if (t2>N) t2=N;
        if ((t1==m_trange[0])&&(t2==m_trange[1]))
            return;
        m_trange=[t1,t2];
        update_plot();
        if (m_do_trigger) {
            m_div.trigger('time-range-changed');
        }
    }

    function set_current_time(t) {
        if (m_current_time == t) return;
        m_current_time=t;
        update_cursor();
        if (m_do_trigger)
            m_div.trigger('current-time-changed');
    }

    function zoom_time(factor) {
        let anchor_time=m_current_time;
        if ((anchor_time<m_trange[0])||(anchor_time>m_trange[1]))
            anchor_time=m_trange[0];
        let old_t1=m_trange[0];
        let old_t2=m_trange[1];
        let t1=anchor_time+(old_t1-anchor_time)/factor;
        let t2=anchor_time+(old_t2-anchor_time)/factor;
        that.setTimeRange(t1,t2);
    }

    function translate_time(dt) {
        let old_t1=m_trange[0];
        let old_t2=m_trange[1];
        let t1=old_t1+dt;
        let t2=old_t2+dt;
        that.setTimeRange(t1,t2);
    }

    function zoom_amplitude(factor) {
        m_y_scale_factor*=factor;
        update_plot();
    }

    function val2pix(ch,t,val) {
        let y0=m_channel_y_positions[ch];
        y0-=(val+m_y_offsets[ch])*m_y_scale_factor*m_channel_spacing/2;
        let xpct=(t-m_trange[0])/(m_trange[1]-m_trange[0]);
        let x0=m_time_axis_xrange[0]+(m_time_axis_xrange[1]-m_time_axis_xrange[0])*xpct;
        return [x0,y0];
    }

    function pix2time(pix) {
        let xpct=(pix[0]-m_time_axis_xrange[0])/(m_time_axis_xrange[1]-m_time_axis_xrange[0]);
        let t=xpct*(m_trange[1]-m_trange[0])+m_trange[0];
        return t;
    }

    function update_size() {
        m_main_canvas.setSize(m_size[0],m_size[1]);
        m_cursor_canvas.setSize(m_size[0],m_size[1]);
        m_time_axis_xrange=[m_margins.left,m_size[0]-m_margins.right];
        m_div.css({width:m_size[0]+'px',height:m_size[1]+'px'})
        update_plot();
    }
    function update_plot() {
        let timer=new Date();
        let M=m_model.numChannels();

        let H0=m_size[1]-m_margins.top-m_margins.bottom;;
        m_channel_spacing=H0/M;
        m_channel_y_positions=[];
        let y0=m_size[1]-m_margins.bottom-m_channel_spacing/2;
        for (let m=0; m<M; m++) {
            m_channel_y_positions.push(y0);
            y0-=m_channel_spacing;
        }

        update_cursor();
        m_main_canvas.update();
    }

    function update_cursor() {
        m_cursor_canvas.update();
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

    function setTimeseriesModel(M) {
        m_model=M;
        auto_scale();
        m_model.onDataSegmentSet(function(ds_factor, t1, t2) {
            if ((t1<=m_trange[1]) && (t2>=m_trange[0])) {
                update_plot();
            }
        });
    }

    function auto_scale() {
        auto_compute_y_offsets();
        auto_compute_y_scale_factor();
    }

    function setSyncGroup(sync_group_name) {
        let sync_groups=window.timeserieswidget_sync_groups;
        if (!(sync_group_name in sync_groups)) {
            sync_groups[sync_group_name]=new SyncGroup();
        }
        let G=sync_groups[sync_group_name];
        G.connect(that);
    }

    function auto_compute_y_offsets() {
        let offsets=[];
        let M=m_model.numChannels();
        for (let m=0; m<M; m++) {
            let data=m_model.getChannelData(m,0,Math.min(m_model.numTimepoints(),5000),1);
            let mean0=compute_mean(data);
            offsets.push(-mean0);
        }
        that.setYOffsets(offsets);
    }

    function auto_compute_y_scale_factor() {
        let vals=[];
        let M=m_model.numChannels();
        for (let m=0; m<M; m++) {
            let data=m_model.getChannelData(m,0,Math.min(m_model.numTimepoints(),5000),1);
            for (let j in data)
                if (!isNaN(data[j])) {
                    vals.push(Math.abs(data[j]+m_y_offsets[m]));
                }
        }
        if (vals.length > 0) {
            vals.sort(function(a, b){return a - b});
            let vv=vals[Math.floor(vals.length*0.9)];
            if (vv>0)
                that.setYScaleFactor(1/(2*vv));
            else
                that.setYScaleFactor(1);
        }
    }

    function handle_mouse_press(X) {
        m_mouse_press_anchor=clone(X);
        m_mouse_press_anchor.trange=clone(m_trange);
    }

    function handle_mouse_release(X) {
        if ((!m_mouse_press_anchor)||(!m_mouse_press_anchor.moving)) {
            let t0=pix2time(X.pos);
            that.setCurrentTime(t0);
        }
        m_mouse_press_anchor=null;
    }

    function handle_mouse_leave(X) {
        m_mouse_press_anchor=null;
    }

    function handle_mouse_move(X) {
        if (m_mouse_press_anchor) {
            if (!m_mouse_handler.moving) {
                let dx=X.pos[0]-m_mouse_press_anchor.pos[0];
                let dy=X.pos[1]-m_mouse_press_anchor.pos[1];
                if (Math.abs(dx)>4) {
                    m_mouse_press_anchor.moving=true;
                }
            }
            
            if (m_mouse_press_anchor.moving) {
                let t1=pix2time(m_mouse_press_anchor.pos);
                let t2=pix2time(X.pos);
                that.setTimeRange(m_mouse_press_anchor.trange[0]+(t1-t2),m_mouse_press_anchor.trange[1]+(t1-t2));
                m_mouse_press_anchor.moving=true;
            }
        }
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
        if (X.delta>0) that.zoomTime(1.15);
        else if (X.delta<0) that.zoomTime(1/1.15);
    }

    that.setTimeseriesModel(new TimeseriesModel({num_channels:0, num_timepoints:0, samplerate:0, segment_size:1000}));
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

function SyncGroup() {
    let that=this;
    this.connect=function(W) {connect(W);};

    let m_widgets=[];

    function connect(W) {
        m_widgets.push(W);
        W.onCurrentTimeChanged(function() {
            m_widgets.forEach(function(W2) {
                W2._triggerOff();
                W2.setCurrentTime(W.currentTime());
                W2._triggerOn();
            })
        });
        W.onTimeRangeChanged(function() {
            let trange = W.timeRange();
            m_widgets.forEach(function(W2) {
                W2._triggerOff();
                W2.setTimeRange(trange[0], trange[1]);
                W2._triggerOn();
            })
        });
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

// Standard Normal variate using Box-Muller transform.
function randn_bm() {
    var u = 0, v = 0;
    while(u === 0) u = Math.random(); //Converting [0,1) to (0,1)
    while(v === 0) v = Math.random();
    return Math.sqrt( -2.0 * Math.log( u ) ) * Math.cos( 2.0 * Math.PI * v );
}

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
