window.CanvasWidget=CanvasWidget;
window.PainterPath=PainterPath;

function CanvasWidget() {
	let O=this;

    O.update=function() {schedule_repaint();};
    O.canvasElement=function() {return m_canvas;};
    O.onPaint=function(handler) {m_paint_handlers.push(handler);};
    O.setSize=function(W,H) {m_size=[W,H]; update_canvas_size();};

    let m_paint_handlers=[];
    let m_size=[100,100];
	var m_canvas=$(document.createElement('canvas'));
	m_canvas.css('position','absolute');
    var m_painter=new CanvasPainter(m_canvas);

	function update_canvas_size() {
		m_canvas[0].width=m_size[0];
		m_canvas[0].height=m_size[1];
		m_canvas.css({
			width:m_size[0],
			height:m_size[1]
		});
		O.update();
    }
    
    let repaint_scheduled=false;
    function schedule_repaint() {
        if (repaint_scheduled) return;
        repaint_scheduled=true;
        setTimeout(function() {
            repaint();
            repaint_scheduled=false;
        },10);
    }

	function repaint() {
        m_painter._initialize(m_size[0],m_size[1]);
        for (let i in m_paint_handlers) {
            m_paint_handlers[i](m_painter);
        }
        m_painter._finalize();
    }
    
    update_canvas_size();
}

function CanvasPainter(canvas) {
	var that=this;
	var ctx=canvas[0].getContext('2d');

	var m_pen={color:'black'};
	var m_font={"pixel-size":12,family:'Arial'};
    var m_brush={color:'black'};
    let m_width=0;
    let m_height=0;

	this.pen=function() {return clone(m_pen);};
	this.setPen=function(pen) {setPen(pen);};
	this.font=function() {return clone(m_font);};
	this.setFont=function(font) {setFont(font);};
	this.brush=function() {return clone(m_brush);};
	this.setBrush=function(brush) {setBrush(brush);};

	this._initialize=function(W,H) {
		//ctx.fillStyle='black';
        //ctx.fillRect(0,0,W,H);
        m_width=W;
        m_height=H;
	};
	this._finalize=function() {
	};
	this.clearRect=function(x,y,W,H) {
		ctx.clearRect(x,y,W,H);
    };
    this.clear=function() {
        ctx.clearRect(0,0,m_width,m_height);
    }
	this.fillRect=function(x,y,W,H,brush) {
		if (typeof brush === 'string') brush={color:brush};
		if (!('color' in brush)) brush={color:brush};
		ctx.fillStyle=to_color(brush.color);
		ctx.fillRect(x,y,W,H);
	};
	this.drawRect=function(x,y,W,H) {
		ctx.strokeStyle=to_color(m_pen.color);
		ctx.strokeRect(x,y,W,H);
	};
	this.drawPath=function(painter_path) {
		ctx.strokeStyle=to_color(m_pen.color);
		painter_path._draw(ctx);
	};
	this.drawLine=function(x1,y1,x2,y2) {
		var ppath=new PainterPath();
		ppath.moveTo(x1,y1);
		ppath.lineTo(x2,y2);
		that.drawPath(ppath);
	};
	this.drawText=function(rect,alignment,txt) {
		var x,y,textAlign,textBaseline;
		if (alignment.AlignLeft) {
			x=rect[0];
			textAlign='left';
		}
		else if (alignment.AlignCenter) {
			x=rect[0]+rect[2]/2;
			textAlign='center';
		}
		else if (alignment.AlignRight) {
			x=rect[0]+rect[2];
			textAlign='right';
		}

		if (alignment.AlignTop) {
			y=rect[1];
			textBaseline='top';
		}
		else if (alignment.AlignBottom) {
			y=rect[1]+rect[3];
			textBaseline='bottom';
		}
		else if (alignment.AlignVCenter) {
			y=rect[1]+rect[3]/2;
			textBaseline='middle';
		}

		ctx.font=m_font['pixel-size']+'px'+' '+m_font.family;
		ctx.textAlign=textAlign;
		ctx.textBaseline=textBaseline;
		ctx.strokeStyle=to_color(m_pen.color);
		ctx.fillStyle=to_color(m_brush.color);
		ctx.fillText(txt,x,y);
	}
	this.drawEllipse=function(rect) {
		ctx.strokeStyle=to_color(m_pen.color);
		ctx.beginPath();
		ctx.ellipse(rect[0]+rect[2]/2,rect[1]+rect[3]/2,rect[2]/2,rect[3]/2,0,0,2*Math.PI);
		ctx.stroke();
	}
	this.fillEllipse=function(rect,brush) {
		if (brush) {
			if (typeof brush === 'string') brush={color:brush};
			if (!('color' in brush)) brush={color:brush};
			ctx.fillStyle=to_color(brush.color);
		}
		else {
			ctx.fillStyle=to_color(m_brush.color);
		}
		ctx.beginPath();
		ctx.ellipse(rect[0]+rect[2]/2,rect[1]+rect[3]/2,rect[2]/2,rect[3]/2,0,0,2*Math.PI);
		ctx.fill();
	}

	function setPen(pen) {
		m_pen=clone(pen);
	}

	function setFont(font) {
		m_font=clone(font);
	}

	function setBrush(brush) {
		m_brush=clone(brush);
	}

	function to_color(col) {
		if (typeof col === 'string') return col;
		return 'rgb('+Math.floor(col[0])+','+Math.floor(col[1])+','+Math.floor(col[2])+')';
	}
}


function PainterPath() {
	this.moveTo=function(x,y) {moveTo(x,y);};
	this.lineTo=function(x,y) {lineTo(x,y);};

	this._draw=function(ctx) {
		ctx.beginPath();
		for (var i=0; i<m_actions.length; i++) {
			apply_action(ctx,m_actions[i]);
		}
		ctx.stroke();
	}
	var m_actions=[];

	function moveTo(x,y) {
		if (y===undefined) {moveTo(x[0],x[1]); return;}
		m_actions.push({
			name:'moveTo',
			x:x,y:y
		});
	}
	function lineTo(x,y) {
        if (m_actions.length==0) {
            moveTo(x,y);
            return;
        }
		if (y===undefined) {lineTo(x[0],x[1]); return;}
		m_actions.push({
			name:'lineTo',
			x:x,y:y
		});
	}

	function apply_action(ctx,a) {
		if (a.name=='moveTo') {
			ctx.moveTo(a.x,a.y);
		}
		else if (a.name=='lineTo') {
			ctx.lineTo(a.x,a.y);
		}
	}
}

function clone(obj) {
    return JSON.parse(JSON.stringify(obj));
}

/**
 * Copyright 2014 Google Inc. All rights reserved.
 *
 * Use of this source code is governed by a BSD-style
 * license that can be found in the LICENSE file.
 *
 * @fileoverview Description of this file.
 *
 * A polyfill for HTML Canvas features, including
 * Path2D support.
 */
if (CanvasRenderingContext2D.prototype.ellipse == undefined) {
  CanvasRenderingContext2D.prototype.ellipse = function(x, y, radiusX, radiusY, rotation, startAngle, endAngle, antiClockwise) {
    this.save();
    this.translate(x, y);
    this.rotate(rotation);
    this.scale(radiusX, radiusY);
    this.arc(0, 0, 1, startAngle, endAngle, antiClockwise);
    this.restore();
  }
}
