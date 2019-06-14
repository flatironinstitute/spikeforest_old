window.Simplot=(function() {
	load_css();
	return {
  	PlotArea:PlotArea,
  	PlotAreaSeries:PlotAreaSeries,
    example1:example1
  }
  
  function inject_css(css) {
  	let style = document.createElement( "style" );
    style.appendChild(document.createTextNode(css));
    document.getElementsByTagName( "head" )[0].appendChild( style );
  }
  
  function load_css() {
    let css=`
.tooltiptext {
  visibility: hidden;
  max-width: 80px;
  /*width: 120px;*/
  background-color: #555;
  color: #fff;
  text-align: center;
  border-radius: 6px;
  padding: 3px 3px;
  position: absolute;
  left: 0px;
  top: 0px;
  z-index: 1;
  border-style: solid;
  border-color: #555 transparent transparent transparent;
}
    `;
    inject_css(css);
  }

  function PlotAreaSeries(x,y,props,opts) {
    let that=this;
    this.initialize=function(gg,plot_area) {initialize(gg,plot_area);}
    this.update=function() {update();};
    this.onMouseOver=function(callback) {m_handlers.mouseover.push(callback);};
    this.onMouseOut=function(callback) {m_handlers.mouseout.push(callback);};
    this.onClick=function(callback) {m_handlers.click.push(callback);};
    this.onMarkerMouseOver=function(callback) {m_handlers.marker_mouseover.push(callback);};
    this.onMarkerMouseOut=function(callback) {m_handlers.marker_mouseout.push(callback);};
    this.onMarkerClick=function(callback) {m_handlers.marker_click.push(callback);};
    this.onTooltipChanged=function(callback) {m_handlers.tooltip_changed.push(callback);};
    this.tooltip=function() {return clone(m_tooltip);};
    this.modifyOpts=function(opts) {modifyOpts(opts);};

    if (!opts) {
      opts=props;
      props=[];
    }

    let m_x=clone(x);
    let m_y=clone(y);
    let m_props=clone(props);
    let m_opts=clone(opts);
    let m_gg=null;
    let m_plot_area=null;
    let m_handlers={
      mouseover:[],
      mouseout:[],
      click:[],
      marker_mouseover:[],
      marker_mouseout:[],
      marker_click:[],
      tooltip_changed:[]
    };
    let m_paths=[];
    let m_markers=[];
    let m_hovering=false;
    let m_marker_hovering=null;
    let m_tooltip={text:'',mouse:[0,0]};
    if (!('lines' in m_opts)) {
      m_opts.lines=true;
    }
    m_opts.line=m_opts.line||{};
    m_opts.marker=m_opts.marker||{};

    function handle_event(name,arg) {
      arg=arg||{};
      m_handlers[name].forEach(function(cb) {cb(arg);});
    }
    function initialize(gg,plot_area) {
      that.onMouseOver(function(a) {
        m_hovering=true;
        update_attributes();
        update_tooltip(a.mouse);
      });
      that.onMouseOut(function(a) {
        m_hovering=false;
        update_attributes();
        update_tooltip(a.mouse);
      });
      that.onMarkerMouseOver(function(a) {
        m_marker_hovering=a.index;
        update_attributes();
        update_tooltip(a.mouse);
      });
      that.onMarkerMouseOut(function(a) {
        m_marker_hovering=null;
        update_attributes();
        update_tooltip(a.mouse);
      });

      m_gg=gg;
      m_plot_area=plot_area;
    }

    function do_modify_obj(obj,obj2) {
      let ret=false;
      for (let key in obj2) {
        let val=obj2[key];
        if (typeof(val)=='object') {
          if (do_modify_obj(obj[key],val)) {
            return true;
          }
        }
        else {
          if (obj[key]!=val) {
            obj[key]=val;
            ret=true;
          }
        }
      }
      return ret;
    }
    function modifyOpts(opts) {
      if (do_modify_obj(m_opts,opts)) {
        update();
      }
    }

    function update() {
      m_gg.selectAll('*').remove();
      let PP=m_plot_area;
      let data0=[];
      for (let i in m_x) {
        data0.push({x:m_x[i],y:m_y[i]});
      }
      m_markers=[];
      m_paths=[];
      let g=m_gg.append('g');
      g.on("mouseover", function() {handle_event('mouseover',{mouse:d3.mouse(this)});})
       .on("mouseout", function() {handle_event('mouseout',{mouse:d3.mouse(this)});})
       .on("click", function() {handle_event('click',{mouse:d3.mouse(this)});});
      if (m_opts.lines) {
        let line=d3.line()
          .x(function(d) {return PP.xToPix(d.x);})
          .y(function(d) {return PP.yToPix(d.y);});
        let path=g.append('path')
          .attr('d',line(data0));
        m_paths.push(path);
      }
      if (m_opts.markers) {
        data0.forEach(function(d,i) {
          let marker=g.append('circle')
            .attr('cx',PP.xToPix(d.x)).attr('cy',PP.yToPix(d.y));
          marker.on("mouseover", function() {handle_event('marker_mouseover',{index:i,mouse:d3.mouse(this)});})
            .on("mouseout", function() {handle_event('marker_mouseout',{index:i,mouse:d3.mouse(this)},this);})
            .on("click", function() {handle_event('marker_click',{index:i,mouse:d3.mouse(this)},this);});
          m_markers.push(marker);
        });
      }
      update_attributes();
    }
    function update_attributes() {
      let line_opts=clone(m_opts.line);
      let marker_opts=clone(m_opts.marker);
      if (m_hovering) {
        let line_hover_opts=line_opts.hover||{};
        for (let key in line_hover_opts) {
          line_opts[key]=line_hover_opts[key];
        }
        let marker_hover_opts=marker_opts.hover||{};
        for (let key in marker_hover_opts) {
          marker_opts[key]=marker_hover_opts[key];
        }
      }

      m_paths.forEach(function(path) {
        let color=line_opts.color||'black';
        ss=path.node().style
        ss.fill="none";
        ss.stroke=color;
        ss['stroke-width']=line_opts.width||1;
      });
      m_markers.forEach(function(marker,i) {
        let opts2=clone(marker_opts); // TODO: improve efficiency for this line
        if (m_props[i]) {
          let oo=clone(m_props[i]);
          let ooh={};
          if (m_marker_hovering === i) {
            ooh=oo.hover||{};
            for (let key in ooh) {
              oo[key]=ooh[key];
            }
          }
          for (let key in oo) {
            opts2[key]=oo[key];
          }
        }
        let radius=opts2['radius']||2;
        let fill=opts2['color']||opts2['fill-color']||'black';
        let stroke=opts2['color']||opts2['stroke-color']||'black';
        marker.attr('r',radius);
        marker.attr('fill',fill).attr('stroke',stroke);
      });
    }
    function update_tooltip(mouse) {
      let str='';
      if (m_hovering) {
        str=m_opts.tooltip||'';
      }
      if (m_marker_hovering !== null) {
        if (m_props[m_marker_hovering]) {
          str=m_props[m_marker_hovering].tooltip||str;
        }
      }
      if (m_tooltip.text != str) {
        m_tooltip={text:str,mouse:mouse};
        handle_event('tooltip_changed');
      }
    }
  }

  function clone(a) {
    return JSON.parse(JSON.stringify(a));
  }

  function same(a,b) {
    return (JSON.stringify(a)==JSON.stringify(b));
  }

  function guidGenerator() {
      var S4 = function() {
         return (((1+Math.random())*0x10000)|0).toString(16).substring(1);
      };
      return (S4()+S4()+"-"+S4()+"-"+S4()+"-"+S4()+"-"+S4()+S4()+S4());
  }

  function PlotArea(svg_elmt) {
    let that=this;

    this.setSize=function(W,H) {setSize(W,H);}
    this.addObject=function(id,obj) {addObject(id,obj);}
    this.removeObject=function(id) {removeObject(id);};
    this.css=function(stye) {css(style);};
    this.setXRange=function(range,dummy) {setXRange(range,dummy);};
    this.setYRange=function(range,dummy) {setYRange(range,dummy);};
    this.xToPix=function(x) {return xToPix(x);};
    this.yToPix=function(y) {return yToPix(y);};
    this.xyToPix=function(xy) {return xyToPix(xy);};
    this.pixToXY=function(pix) {return pixToXY(pix);};
    this.pixToX=function(pix) {return pixToX(pix);};
    this.pixToY=function(pix) {return pixToY(pix);};
    this.bringObjectToFront=function(id) {bringObjectToFront(id);};

    let m_width=100;
    let m_height=100;
    let m_objects={};
    let m_x_range=[0,0];
    let m_y_range=[0,0];
    let m_tooltip_div=document.createElement('div');
    m_tooltip_div.setAttribute('class','tooltiptext');
    document.body.appendChild(m_tooltip_div);

    function setSize(W,H) {
      m_width=W;
      m_height=H;
      update_attributes();
    }

    function xToPix(x) {
      let pct=(x-m_x_range[0])/(m_x_range[1]-m_x_range[0]);
      return pct*m_width;
    }
    function yToPix(y) {
      let pct=(y-m_y_range[0])/(m_y_range[1]-m_y_range[0]);
      return (1-pct)*m_height;
    }
    function xyToPix(xy) {
      return [xToPix(xy[0]),yToPix(xy[1])];
    }
    function pixToX(pix) {
      let pct=pix/m_width;
      return m_x_range[0]+pct*(m_x_range[1]-m_x_range[0]);
    }
    function pixToY(pix) {
      let pct=1-pix/m_height;
      return m_y_range[0]+pct*(m_y_range[1]-m_y_range[0]);
    }
    function pixToXY(pix) {
      return [pixToX(pix[0]),pixToY(pix[1])];
    }

    function setXRange(range,dummy) {
      if (dummy) range=[range,dummy];
      if (same(range,m_x_range)) return;
      m_x_range=clone(range);
      schedule_refresh();
    }
    function setYRange(range,dummy) {
      if (dummy) range=[range,dummy];
      if (same(range,m_y_range)) return;
      m_y_range=clone(range);
      schedule_refresh();
    }

    function update_attributes() {
      d3.select(svg_elmt)
        .attr('width',m_width).attr('height',m_height);
    }
    function addObject(id,obj) {
      if (!obj) {obj=id; id=null;}
      if (!id) {id=guidGenerator();}
      if (!(id in m_objects)) {
        m_objects[id]={
          gg:d3.select(svg_elmt).append('g'),
          object:null
        };
      }

      let gg=m_objects[id].gg;
      gg.selectAll('*').remove();
      m_objects[id].object=obj;
      obj.initialize(gg,that);

      if (obj.onTooltipChanged) {
        obj.onTooltipChanged(update_tooltip);
      }
      update_tooltip();
      schedule_refresh();
    }
    function bringObjectToFront(id) {
      if (!(id in m_objects)) return;
      let gg=m_objects[id].gg;
      gg.node().parentNode.appendChild(gg.node());
      //d3.select(svg_elmt).appendChild(gg);
    }
    function update_tooltip() {
      let the_tooltip={text:'',mouse:[0,0]};
      for (let id in m_objects) {
        let obj=m_objects[id].object;
        if (obj.tooltip) {
          let tt=obj.tooltip();
          if ((tt)&&(tt.text)) {
            the_tooltip=tt;
          }
        }
      }

      let elmt=m_tooltip_div;
      elmt.innerHTML=the_tooltip.text;
      elmt.style.left=(the_tooltip.mouse[0]+18)+'px';
      elmt.style.top=(the_tooltip.mouse[1]+18)+'px';
      if (the_tooltip.text) {
        elmt.style.visibility='visible';
      }
      else {
        elmt.style.visibility='hidden';
      }
    }
    function removeObject(id) {
      if (m_objects[id]) {
        m_objects[id].gg.remove();
        delete m_objects[id];
      }
      update_tooltip();
    }
    function css(style) {
      for (let key in style) {
        d3.select(svg_elmt)
        .style(key,style[key])
      }
    }

    let _refresh_scheduled=false;
    function schedule_refresh() {
      if (_refresh_scheduled) return;
      _refresh_scheduled=true;
      setTimeout(function() {
        _refresh_scheduled=false;
        do_refresh();
      },10);
      function do_refresh() {
        if ((m_x_range[0]==m_x_range[1])||(m_y_range[0]==m_y_range[1]))
          return;
        for (let id in m_objects) {
          m_objects[id].object.update();
        }
      }
    }

    update_attributes();
  }

  ///////////////////////////////////////////////////////////////////////////////////////////////////////
  function example1(svg_id) {
    P=new Simplot.PlotArea(document.getElementById(svg_id));
    P.setXRange(-100,100);
    P.setYRange(-100,100);
    P.setSize(250,250);

    function range(start, count) {
      if (arguments.length == 1) {count = start; start = 0;}
      var foo = [];
      for (var i = 0; i < count; i++) {foo.push(start + i);}
      return foo;
    }

    let Nth=10;
    let theta=range(Nth+1).map(function(v) {return v*2*Math.PI/Nth});
    let x=theta.map(function(v) {return 20*Math.cos(v);});
    let y=theta.map(function(v) {return 20*Math.sin(v);});
    let props=theta.map(function(v,i) {if (i==1) return {color:'blue',tooltip:'i=1',hover:{color:'red'}}; else return {};});
    let opts={
      marker:{
        color:'pink',
        radius:4
      },
      line:{
        color:'lightgreen',
        width:2,
        hover:{
          color:'darkgreen',
          width:3
        }
      },
      tooltip:'testing --- this is a test tooltip',
      lines:true,
      markers:true  
    };
    let ct=0;
    function next() {
      x=x.map(function(v) {v+=5; if (v>100) v-=100; return v;})
      y=y.map(function(v) {v+=10; if (v>100) v-=100; return v;})

      series=new Simplot.PlotAreaSeries(x,y,props,opts);
      /*
      series.onMouseOver(function() {console.log('over')});
      series.onMouseOut(function() {console.log('out')});
      series.onClick(function() {console.log('click')});
      series.onMarkerMouseOver(function(i) {console.log('marker over',i)});
      series.onMarkerMouseOut(function(i) {console.log('marker out',i)});
      */
      series.onMarkerClick(function(i) {console.log('marker click',i)});
      P.addObject('id1',series);
      ct++;
      setTimeout(next,1000);
    }
    next();
  }
})();
