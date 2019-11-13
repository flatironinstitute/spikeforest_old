export function CanvasPainter(context2d) {
    var that = this;
    var ctx = context2d;

    var m_pen = { color: 'black' };
    var m_font = { "pixel-size": 12, family: 'Arial' };
    var m_brush = { color: 'black' };
    let m_width = 0;
    let m_height = 0;

    this.pen = function () { return clone(m_pen); };
    this.setPen = function (pen) { setPen(pen); };
    this.font = function () { return clone(m_font); };
    this.setFont = function (font) { setFont(font); };
    this.brush = function () { return clone(m_brush); };
    this.setBrush = function (brush) { setBrush(brush); };

    this._initialize = function (W, H) {
        //ctx.fillStyle='black';
        //ctx.fillRect(0,0,W,H);
        m_width = W;
        m_height = H;
    };
    this._finalize = function () {
    };
    this.clearRect = function (x, y, W, H) {
        ctx.clearRect(x, y, W, H);
    };
    this.clear = function () {
        ctx.clearRect(0, 0, m_width, m_height);
    }
    this.fillRect = function (x, y, W, H, brush) {
        if (typeof brush === 'string') brush = { color: brush };
        if (!('color' in brush)) brush = { color: brush };
        ctx.fillStyle = to_color(brush.color);
        ctx.fillRect(x, y, W, H);
    };
    this.drawRect = function (x, y, W, H) {
        ctx.strokeStyle = to_color(m_pen.color);
        ctx.strokeRect(x, y, W, H);
    };
    this.drawPath = function (painter_path) {
        ctx.strokeStyle = to_color(m_pen.color);
        painter_path._draw(ctx);
    };
    this.drawLine = function (x1, y1, x2, y2) {
        var ppath = new PainterPath();
        ppath.moveTo(x1, y1);
        ppath.lineTo(x2, y2);
        that.drawPath(ppath);
    };
    this.drawText = function (rect, alignment, txt) {
        var x, y, textAlign, textBaseline;
        if (alignment.AlignLeft) {
            x = rect[0];
            textAlign = 'left';
        }
        else if (alignment.AlignCenter) {
            x = rect[0] + rect[2] / 2;
            textAlign = 'center';
        }
        else if (alignment.AlignRight) {
            x = rect[0] + rect[2];
            textAlign = 'right';
        }

        if (alignment.AlignTop) {
            y = rect[1];
            textBaseline = 'top';
        }
        else if (alignment.AlignBottom) {
            y = rect[1] + rect[3];
            textBaseline = 'bottom';
        }
        else if (alignment.AlignVCenter) {
            y = rect[1] + rect[3] / 2;
            textBaseline = 'middle';
        }

        ctx.font = m_font['pixel-size'] + 'px ' + m_font.family;
        ctx.textAlign = textAlign;
        ctx.textBaseline = textBaseline;
        ctx.strokeStyle = to_color(m_pen.color);
        ctx.fillStyle = to_color(m_brush.color);
        ctx.fillText(txt, x, y);
    }
    this.drawEllipse = function (rect) {
        ctx.strokeStyle = to_color(m_pen.color);
        ctx.beginPath();
        ctx.ellipse(rect[0] + rect[2] / 2, rect[1] + rect[3] / 2, rect[2] / 2, rect[3] / 2, 0, 0, 2 * Math.PI);
        ctx.stroke();
    }
    this.fillEllipse = function (rect, brush) {
        if (brush) {
            if (typeof brush === 'string') brush = { color: brush };
            if (!('color' in brush)) brush = { color: brush };
            ctx.fillStyle = to_color(brush.color);
        }
        else {
            ctx.fillStyle = to_color(m_brush.color);
        }
        ctx.beginPath();
        ctx.ellipse(rect[0] + rect[2] / 2, rect[1] + rect[3] / 2, rect[2] / 2, rect[3] / 2, 0, 0, 2 * Math.PI);
        ctx.fill();
    }

    function setPen(pen) {
        m_pen = clone(pen);
    }

    function setFont(font) {
        m_font = clone(font);
    }

    function setBrush(brush) {
        m_brush = clone(brush);
    }

    function to_color(col) {
        if (typeof col === 'string') return col;
        return 'rgb(' + Math.floor(col[0]) + ',' + Math.floor(col[1]) + ',' + Math.floor(col[2]) + ')';
    }
}

export function PainterPath() {
    this.moveTo = function (x, y) { moveTo(x, y); };
    this.lineTo = function (x, y) { lineTo(x, y); };

    this._draw = function (ctx) {
        ctx.beginPath();
        for (var i = 0; i < m_actions.length; i++) {
            apply_action(ctx, m_actions[i]);
        }
        ctx.stroke();
    }
    var m_actions = [];

    function moveTo(x, y) {
        if (y === undefined) { moveTo(x[0], x[1]); return; }
        m_actions.push({
            name: 'moveTo',
            x: x, y: y
        });
    }
    function lineTo(x, y) {
        if (m_actions.length === 0) {
            moveTo(x, y);
            return;
        }
        if (y === undefined) { lineTo(x[0], x[1]); return; }
        m_actions.push({
            name: 'lineTo',
            x: x, y: y
        });
    }

    function apply_action(ctx, a) {
        if (a.name === 'moveTo') {
            ctx.moveTo(a.x, a.y);
        }
        else if (a.name === 'lineTo') {
            ctx.lineTo(a.x, a.y);
        }
    }
}

export function MouseHandler() {
    this.setElement=function(elmt) {m_element=elmt;};
    this.onMousePress=function(handler) {m_handlers['press'].push(handler);};
    this.onMouseRelease=function(handler) {m_handlers['release'].push(handler);};
    this.onMouseMove=function(handler) {m_handlers['move'].push(handler);};
    this.onMouseEnter=function(handler) {m_handlers['enter'].push(handler);};
    this.onMouseLeave=function(handler) {m_handlers['leave'].push(handler);};
    this.onMouseWheel=function(handler) {m_handlers['wheel'].push(handler);};

    this.mouseDown=function(e) {report('press',mouse_event(e)); return true;};
    this.mouseUp=function(e) {report('release',mouse_event(e)); return true;};
    this.mouseMove=function(e) {report('move',mouse_event(e)); return true;};
    this.mouseEnter=function(e) {report('enter',mouse_event(e)); return true;};
    this.mouseLeave=function(e) {report('leave',mouse_event(e)); return true;};
    this.mouseWheel=function(e) {report('wheel', wheel_event(e)); return true;};
    // elmt.on('dragstart',function() {return false;});
    // elmt.on('mousewheel', function(e){report('wheel',wheel_event($(this),e)); return false;});

    let m_element=null;
    let m_handlers={
        press:[],release:[],move:[],enter:[],leave:[],wheel:[]
    };

    function report(name,X) {
        for (let i in m_handlers[name]) {
            m_handlers[name][i](X);
        }
    }

    function mouse_event(e) {
        if (!m_element) return null;
        //var parentOffset = $(this).parent().offset(); 
        //var offset=m_element.offset(); //if you really just want the current element's offset
        var rect = m_element.getBoundingClientRect();
        window.m_element=m_element;
        window.dbg_m_element = m_element;
        window.dbg_e = e;
        var posx = e.clientX - rect.x;
        var posy = e.clientY - rect.y;
        return {
            pos:[posx,posy],
            modifiers:{ctrlKey:e.ctrlKey}
        };
    }
    function wheel_event(e) {
        return {
            delta:e.originalEvent.wheelDelta
        };
    }
}

function clone(obj) {
    return JSON.parse(JSON.stringify(obj));
}
