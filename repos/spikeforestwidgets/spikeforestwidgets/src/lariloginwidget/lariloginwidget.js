import React from "react";
import ReactDOM from "react-dom";
import { SelectList } from 'react-widgets';
import 'react-widgets/dist/css/react-widgets.css';
let LariClient=require('lariclient').v1;

class LariLoginWidget extends React.Component {
	constructor(props) {
    super(props);
    this._passcode_lookup=load_passcode_lookup();
    this.state = {selected_server:null,LARI_ID:'',LARI_PASSCODE:'',node_infos:{}};
    if ((props.servers)&&(props.servers.length>0)) {
    	this.state.selected_server=props.servers[0];
    	this.state.LARI_ID=props.servers[0].LARI_ID;
    	this.state.LARI_PASSCODE=this._passcode_lookup[this.state.LARI_ID]||'';
    }

    this.handle_passcode_change = this.handle_passcode_change.bind(this);
    this.update_node_infos();
  }

  handle_passcode_change(event) {
		let passcode=event.target.value;
		let state=JSON.parse(JSON.stringify(this.state));
		if (state.LARI_ID) {
			state.LARI_PASSCODE=passcode;
			this._passcode_lookup[this.state.LARI_ID]=passcode;
			save_passcode_lookup(this._passcode_lookup);
		}
		this.setState(state);
		this.props.onStateChanged(state);
  }

  async update_node_infos() {
		let LC=new LariClient();
		let {
			servers
		} = this.props;
		for (let i in servers) {
			let S=servers[i];
			let lari_id=S.LARI_ID;
			if (lari_id) {
				{
		  		let state=JSON.parse(JSON.stringify(this.state));
		  		state.node_infos[lari_id]={status:'checking'};
		  		this.setState(state);
		  	}

				let info;
				try {
					info=await LC.getNodeInfo(lari_id);
				}
				catch(err) {
					info={status:'error',error:err.message};	
				}

				{
		  		let state=JSON.parse(JSON.stringify(this.state));
		  		state.node_infos[lari_id]=info;
		  		this.setState(state);
		  	}
		  }
		}
	}

  render() {
  	let that=this;
  	let {
  		servers
  	} = this.props;

  	if (!servers) {
  		servers=default_servers();
  	}

		let ListItem = function({item}) {
  		let info0=that.state.node_infos[item.LARI_ID]||{};
  		let status0=<span></span>
  		if (info0.status=='checking') {
  			status0=<span style={{color:'orange'}}>[{info0.status}]</span>
  		}
  		else if (info0.status=='error') {
  			status0=<span style={{color:'red'}} title={info0.error}>[not found]</span>
  		}
  		else if (info0.node_id) {
  			status0=<span style={{color:'green'}}>[found]</span>	
  		}
  		return <span>
		    {item.label}&nbsp;
		    {status0}
		  </span>;
  	}

		let passcode_element=<span></span>
		let visibility='hidden'
		if ((this.state.selected_server)&&(this.state.LARI_ID)) {
			visibility='visible';
		}
		passcode_element=
				<div style={{visibility:visibility,"margin-top":'5px'}}>
				  Passcode for {(this.state.selected_server||{}).label}:&nbsp;
				  <input type="password"
				  	onChange={this.handle_passcode_change}
				  	value={this.state.LARI_PASSCODE}
				  >
				  </input>
				</div>;

		let div_style={
			overflow:'auto',
			height:150,
			width:600,
			border:'solid 1px gray'
		};
  	return (
  		<div style={{height:240}}>
	  		<h3>Select processing server</h3>
	  		<div style={div_style}>
				  <SelectList
				    data={servers}
				    textField='label'
				    valueField='LARI_ID'
				    value={this.state.LARI_ID}
				    onChange={
				    	(value) => {
				    		let state={ 
				    			selected_server:value,
				    			LARI_ID:value.LARI_ID||'',
				    			LARI_PASSCODE:this._passcode_lookup[value.LARI_ID||'']||''
				    		};
				    		this.setState(state);
				    		this.props.onStateChanged(state);
				    	}
				    }
				    itemComponent={ListItem}
				  />
			  </div>
		  	{passcode_element}
		  </div>
		);
	}
}

function default_servers() {
	let servers=[];
	servers.push({
		label:'local computer',
		LARI_ID:''
	});
	return servers;
}

function load_passcode_lookup() {
	try {
		return JSON.parse(localStorage.passcode_lookup);
	}
	catch(err) {
		return {};
	}
}

function save_passcode_lookup(X) {
	try {
		return localStorage.passcode_lookup=JSON.stringify(X);
	}
	catch(err) {
	}	
}

module.exports=LariLoginWidget