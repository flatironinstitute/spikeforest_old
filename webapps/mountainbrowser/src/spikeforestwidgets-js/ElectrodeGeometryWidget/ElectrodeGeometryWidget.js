import React, { Component } from "react";
import { CanvasPainter, MouseHandler } from "../common/CanvasPainter";

export default class ElectrodeGeometryWidget extends Component {
    constructor(props) {
        super(props);
        this.state = {
        }
        this.xmin = 0;
        this.xmax = 1;
        this.ymin = 0;
        this.ymax = 2;
        this.transpose = false;
        this.margins = { top: 15, bottom: 15, left: 15, right: 15 };
        this.channel_rects = {};
        this.hovered_electrode_index = -1;
        this.current_electrode_index = -1;
        this.canvasRef = React.createRef();
        this.mouseHandler = new MouseHandler();

        this.mouseHandler.onMousePress(this.handleMousePress);
        this.mouseHandler.onMouseRelease(this.handleMouseRelease);
        this.mouseHandler.onMouseMove(this.handleMouseMove);
    }

    componentDidMount() {
        this.repaint()
    }

    componentDidUpdate() {
        this.repaint()
    }

    determineWidthHeight() {
        this.updatePositions();

        let W = this.props.width;
        let H = this.props.height;
        if (!H) {
            let x1 = this.xmin - this.mindist, x2 = this.xmax + this.mindist;
            let y1 = this.ymin - this.mindist, y2 = this.ymax + this.mindist;
            let w0 = x2 - x1, h0 = y2 - y1;
            if (this.transpose) {
                let w0_tmp = w0;
                w0 = h0;
                h0 = w0_tmp;
            }
            if (!w0) {
                H = 100;
            }
            else {
                H = h0 / w0 * W;
            }
        }
        return { width: W, height: H };
    }

    repaint = () => {
        const { width, height } = this.determineWidthHeight();
        const canvas = this.canvasRef.current;
        if (!canvas) return;
        const ctx = canvas.getContext('2d');

        this.mouseHandler.setElement(canvas);

        let painter = new CanvasPainter(ctx);
        let W = width;
        let H = height;

        painter.clearRect(0, 0, W, H);

        let W1 = W, H1 = H;
        if (this.transpose) {
            W1 = H;
            H1 = W;
        }

        let x1 = this.xmin - this.mindist, x2 = this.xmax + this.mindist;
        let y1 = this.ymin - this.mindist, y2 = this.ymax + this.mindist;
        let w0 = x2 - x1, h0 = y2 - y1;
        let offset, scale;
        if (w0 * H1 > h0 * W1) {
            scale = W1 / w0;
            offset = [0 - x1 * scale, (H1 - h0 * scale) / 2 - y1 * scale];
        } else {
            scale = H1 / h0;
            offset = [(W1 - w0 * scale) / 2 - x1 * scale, 0 - y1 * scale];
        }
        this.channel_rects = {};
        if (this.props.locations) {
            for (let i in this.props.locations) {
                let pt0 = this.props.locations[i];
                let x = pt0[0] * scale + offset[0];
                let y = pt0[1] * scale + offset[1];
                let rad = this.mindist * scale / 3;
                let x1 = x, y1 = y;
                if (this.transpose) {
                    x1 = y;
                    y1 = x;
                }
                let col = this.getChannelColor(i);
                let rect0 = [x1 - rad, y1 - rad, rad * 2, rad * 2];
                painter.fillEllipse(rect0, col);
                this.channel_rects[i] = rect0;
                let label0;
                if (this.props.labels) {
                    label0 = this.props.labels[i] || '';
                }
                else {
                    label0 = '';
                }
                if ((label0) || (label0 === 0)) {
                    painter.setBrush({ color: 'white' });
                    painter.setFont({ 'pixel-size': rad });
                    painter.drawText(rect0, { AlignCenter: true, AlignVCenter: true }, label0);
                }
            }
        }
    }

    updatePositions() {
        if (!this.props.locations) {
            return;
        }
        let pt0 = this.props.locations[0] || [0, 0];
        let xmin = pt0[0], xmax = pt0[0];
        let ymin = pt0[1], ymax = pt0[1];
        for (let i in this.props.locations) {
            let pt = this.props.locations[i];
            xmin = Math.min(xmin, pt[0]);
            xmax = Math.max(xmax, pt[0]);
            ymin = Math.min(ymin, pt[1]);
            ymax = Math.max(ymax, pt[1]);
        }
        // if (xmax === xmin) xmax++;
        // if (ymax === ymin) ymax++;

        this.xmin = xmin; this.xmax = xmax;
        this.ymin = ymin; this.ymax = ymax;

        this.transpose = (this.ymax - this.ymin > this.xmax - this.xmin);

        let mindists = [];
        for (var i in this.props.locations) {
            let pt0 = this.props.locations[i];
            let mindist = -1;
            for (let j in this.props.locations) {
                let pt1 = this.props.locations[j];
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
        this.mindist = avg_mindist;
    }

    getChannelColor(ind) {
        let color = 'rgb(0, 0, 255)';
        let color_hover = 'rgb(100, 100, 255)';
        let color_current = 'rgb(200, 200, 100)';
        let color_current_hover = 'rgb(220, 220, 150)';

        if (ind === this.current_electrode_index) {
            if (ind === this.hovered_electrode_index) return color_current_hover;
            else return color_current;
        }
        else {
            if (ind === this.hovered_electrode_index) return color_hover;
            else return color;
        }
    }

    electrodeIndexAtPixel(pos) {
        for (let i in this.channel_rects) {
            let rect0 = this.channel_rects[i];
            if ((rect0[0] <= pos[0]) && (pos[0] <= rect0[0] + rect0[2])) {
                if ((rect0[1] <= pos[1]) && (pos[1] <= rect0[1] + rect0[2])) {
                    return i;
                }
            }
        }
        return -1;
    }

    setHoveredElectrodeIndex(ind) {
        if (ind === this.hovered_electrode_index)
            return;
        this.hovered_electrode_index = ind;
        this.repaint()
    }

    handleMousePress = (X) => {
    }

    handleMouseRelease = (X) => {
    }

    handleMouseMove = (X) => {
        if (!X) return;
        let elec_ind = this.electrodeIndexAtPixel(X.pos);
        this.setHoveredElectrodeIndex(elec_ind);
    }

    render() {
        const { width, height } = this.determineWidthHeight();

        // We'll need to think of a better way to do this
        setTimeout(this.repaint, 100);

        let canvas = <canvas
            ref={this.canvasRef}
            width={width}
            height={height}
            onMouseDown={this.mouseHandler.mouseDown}
            onMouseUp={this.mouseHandler.mouseUp}
            onMouseMove={this.mouseHandler.mouseMove}
        />

        if (this.props.locations === undefined) {
            return <span>
                <div>Loading...</div>
                {canvas}
            </span>
        }
        else if (this.props.locations === null) {
            return <span>
                <div>Not found.</div>
                {canvas}
            </span>
        }

        return canvas;
    }
}

function compute_average(list) {
    if (list.length === 0) return 0;
    var sum = 0;
    for (var i in list) sum += list[i];
    return sum / list.length;
}
