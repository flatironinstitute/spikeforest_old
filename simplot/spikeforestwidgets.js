window.SpikeforestWidgets=(function() {
	return {
		SpikeWaveformsWidget:SpikeWaveformsWidget,
		example1:example1
	};

	function range(start, count) {
      if (arguments.length == 1) {count = start; start = 0;}
      var foo = [];
      for (var i = 0; i < count; i++) {foo.push(start + i);}
      return foo;
  }

	function SpikeWaveformsWidget(div) {
		let that=this;
		this.setSize=function(W,H) {setSize(W,H);};
		this.setGeometry=function(geom) {m_geometry=clone(geom); schedule_update_spikes();}; //should be done prior to adding spikes
		this.setYRange=function(min,max) {m_y_range=[min,max]; schedule_update_spikes();};
		this.setChannelSpacing=function(dx,dy) {m_channel_spacing=[dx,dy]; schedule_update_spikes();};
		this.addSpike=function(id,data) {addSpike(id,data);};

		let m_svg=$('<svg width=200 height=200 />'); //apparently important to intialize this with some initial size
		$(div).append(m_svg);
		let m_plot=new Simplot.PlotArea(m_svg[0]);
		let m_spikes={};
		let m_current_spike_id=null;
		let m_hovered_spike_id=null;
		let m_geometry=null;
		let m_channel_areas=null;
		let m_channel_spacing=null;
		let m_y_range=null;

		function setSize(W,H) {
			m_plot.setSize(W,H);
		}
		function set_current_spike_id(id) {
			if (m_current_spike_id==id) return;
			m_current_spike_id=id;
			update_spike_colors_and_order();
		}
		function set_hovered_spike_id(id) {
			if (m_hovered_spike_id==id) return;
			m_hovered_spike_id=id;
			update_spike_colors_and_order();
		}
		function update_spike_colors_and_order() {
			if (m_hovered_spike_id) bring_spike_to_front(m_hovered_spike_id);
			if (m_current_spike_id) bring_spike_to_front(m_current_spike_id);
			for (let id2 in m_spikes) {
				let opts0={line:{color:'gray',width:1}};
				if (id2==m_current_spike_id) {
				//	opts0={line:{color:'green',width:2}};
				}
				else if (id2==m_hovered_spike_id) {
					opts0={line:{color:'blue'}};
				}
				for (let jj in m_spikes[id2].plot_series) {
					m_spikes[id2].plot_series[jj].modifyOpts(opts0);
				}
			}
		}
		function addSpike(id,data) {
			m_spikes[id]={
				data:clone(data),
				plot_series:null
			}
			set_current_spike_id(id);
			schedule_update_spikes();
		}
		function compute_max_abs(x) {
			let ret=x[0];
			for (let i in x) {
				if (Math.abs(x[i])<ret) ret=Math.abs(x[i]);
			}
			return ret;
		}
		function compute_min(x) {
			let ret=x[0];
			for (let i in x) {
				if (x[i]<ret) ret=x[i];
			}
			return ret;
		}
		function compute_max(x) {
			let ret=x[0];
			for (let i in x) {
				if (x[i]>ret) ret=x[i];
			}
			return ret;
		}
		function auto_compute_channel_spacing() {
			let num_channels=m_geometry.length;
			let xcoords=[];
			let ycoords=[];
			for (let m=0; m<num_channels; m++) {
				xcoords.push(m_geometry[m][0]);
				ycoords.push(m_geometry[m][1]);
			}
			xcoords.sort();
			ycoords.sort();
			let xspacing=null;
			let yspacing=null;
			for (let i=0; i<xcoords.length-1; i++) {
				let xdist=xcoords[i+1]-xcoords[i];
				let ydist=ycoords[i+1]-ycoords[i];
				if (xdist>0) {
					if ((xspacing===null)||(xdist<xspacing)) xspacing=xdist;
				}
				if (ydist>0) {
					if ((yspacing===null)||(ydist<yspacing)) yspacing=ydist;
				}
			}
			if (xspacing===null) xspacing=1;
			if (yspacing===null) yspacing=1;
			let count=0;
			while (count<10) {
				let min_xdist=null;
				let min_ydist=null;
				for (let m=0; m<num_channels; m++) {
					let min_xdist_m=null;
					let min_ydist_m=null;
					for (let m2=0; m2<num_channels; m2++) {
						if (m2!=m) {
							if (Math.abs(m_geometry[m][1]-m_geometry[m2][1])<yspacing*0.9) {
								let tmp=Math.abs(m_geometry[m][0]-m_geometry[m2][0]);
								if (tmp>0) {
									if ((min_xdist_m===null)||(tmp<min_xdist_m)) min_xdist_m=tmp;
								}
							}
							/*
							if (Math.abs(m_geometry[m][0]-m_geometry[m2][0])<xspacing*0.9) {
								let tmp=Math.abs(m_geometry[m][1]-m_geometry[m2][1]);
								if (tmp>0) {
									if ((min_ydist_m===null)||(tmp<min_ydist_m)) min_ydist_m=tmp;
								}
							}
							*/
						}
					}
					if ((min_xdist===null)||(min_xdist_m<min_xdist)) min_xdist=min_xdist_m;
					if ((min_ydist===null)||(min_ydist_m<min_ydist)) min_ydist=min_ydist_m;
				}
				if (min_xdist===null) min_xdist=xspacing;
				if (min_ydist===null) min_ydist=yspacing;
				if ((xspacing==min_xdist)&&(yspacing==min_ydist)) {
					break;
				}
				xspacing=min_xdist;
				yspacing=min_ydist;
				count++;
			}
			return [xspacing,yspacing];
		}

		function percentile(x,pct) {
			let ind=Math.floor(x.length*pct/100);
			if (ind>=x.length) ind=x.length-1;
			return x[ind];
		}
		function auto_compute_y_range() {
			let num_channels=m_geometry.length;
			let min_values=[];
			let max_values=[];
			for (let id in m_spikes) {
				let data=m_spikes[id].data;
				let min0=0;
				let max0=0;
				for (let m=0; m<num_channels; m++) {
					let min=compute_min(data[m]);
					let max=compute_max(data[m]);
					if (min<min0) min0=min;
					if (max>max0) max0=max;
				}
				min_values.push(min0);
				max_values.push(max0);
			}
			min_values.sort();
			max_values.sort();
			return [percentile(min_values,20),percentile(max_values,80)];
		}

		function update_channel_areas() {
			let y_range=m_y_range;
			if (y_range===null) {
				y_range=auto_compute_y_range();
			}
			let channel_spacing=m_channel_spacing;
			if (channel_spacing===null) {
				channel_spacing=auto_compute_channel_spacing();
			}
			let num_channels=m_geometry.length;
			m_channel_areas=[];
			for (let m=0; m<num_channels; m++) {
				let area={};
				area.xmin=m_geometry[m][0]-channel_spacing[0]/2*0.8;
				area.xmax=m_geometry[m][0]+channel_spacing[0]/2*0.8;
				area.ymin=m_geometry[m][1]-channel_spacing[1]/2*0.8;
				area.ymax=m_geometry[m][1]+channel_spacing[1]/2*0.8;
				area.range=[y_range[0],y_range[1]];
				m_channel_areas.push(area);
			}
			let xmin=null;
			let xmax=null;
			let ymin=null;
			let ymax=null;
			for (let i=0; i<m_channel_areas.length; i++) {
				let area=m_channel_areas[i];
				if ((xmin===null)||(area.xmin<xmin)) xmin=area.xmin;
				if ((xmax===null)||(area.xmax>xmax)) xmax=area.xmax;
				if ((ymin===null)||(area.ymin<ymin)) ymin=area.ymin;
				if ((ymax===null)||(area.ymax>ymax)) ymax=area.ymax;
			}
			m_plot.setXRange(xmin,xmax);
			m_plot.setYRange(ymin,ymax);
		}
		function bring_spike_to_front(id) {
			for (let jj in m_spikes[id].plot_series) {
				let PP=m_spikes[id].plot_series[jj];
				m_plot.bringObjectToFront(PP.object_id);
			}
		}
		function do_update_spikes() {
			update_channel_areas();
			let ids=Object.keys(m_spikes);
			ids.forEach(function(id) {
				if (!m_spikes[id].plot_series) {
					let data=m_spikes[id].data;
					m_spikes[id].plot_series=[];
					let num_channels=data.length;
					let snippet_length=data[0].length;
					let opts={
						line:{
							width:2,
							color:'lightgray'
						}
					};
					for (let m=0; m<num_channels; m++) {
						let area=m_channel_areas[m];
						let xx=[];
						let yy=[];
						for (let t=0; t<snippet_length; t++) {
							xx.push(area.xmin+(area.xmax-area.xmin)*t/snippet_length);
							let pct=(data[m][t]-area.range[0])/(area.range[1]-area.range[0]);
							yy.push(area.ymin+(area.ymax-area.ymin)*pct);
						}
						let PP=new Simplot.PlotAreaSeries(xx,yy,[],opts);
						PP.object_id='spike-'+id+'-channel-'+m;
						m_plot.addObject(PP.object_id,PP);
						m_spikes[id].plot_series.push(PP);
					}

					m_spikes[id].plot_series.forEach(function(PP) {
						PP.onMouseOver(function() {
							set_hovered_spike_id(id);
						});
						PP.onMouseOut(function() {
							if (m_hovered_spike_id==id) {
								set_hovered_spike_id(null);
							}
						});
						PP.onClick(function() {
							set_current_spike_id(id);
						});
					});
				}
			});
			update_spike_colors_and_order();
		}
		let _update_spikes_scheduled=false;
		function schedule_update_spikes() {
			if (_update_spikes_scheduled) return;
			_update_spikes_scheduled=true;
			setTimeout(function() {
				_update_spikes_scheduled=false;
				do_update_spikes();
			},100);
		}
	}

	function clone(a) {
    return JSON.parse(JSON.stringify(a));
  }

  function same(a,b) {
    return (JSON.stringify(a)==JSON.stringify(b));
  }

	function example1(div_id) {
		let W=new SpikeWaveformsWidget(document.getElementById(div_id));
		W.setSize(400,400);
		let geom=[[0.5,1],[1.5,1],[0,0],[1,0],[2,0],[0.5,-1],[1.5,-1]];
		W.setGeometry(geom);
		//W.setChannelSpacing(10,10);
		//W.setYRange(-30,30);
		let num_channels=geom.length;
		let tmp1=[0,1,2,3,4,6,12,20,12,6,4,3,2,1,0];
		let tmp2=[0,1,2,3,4,6,12,5,12,6,4,3,2,1,0];
		let data=[tmp1,tmp2,tmp2,tmp2,tmp2,tmp2,tmp2,tmp2];
		let noise_level=5;
		let num_spikes=35;
		for (let i=0; i<num_spikes; i++) {
			let data0=[];
			for (let m=0; m<num_channels; m++) {
				data0.push(data[m].map(function(v) {return v+Math.random()*noise_level;}));
			}
			W.addSpike('spike-'+i,data0);	
		}
	}
})();