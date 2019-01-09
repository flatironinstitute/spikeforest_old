//import React from "react";
//import ReactDOM from "react-dom";

//import $ from 'jquery';
//window.jQuery = $;
//window.$ = $;

/*
const registered_widgets={
	DatasetSelectWidget:require(__dirname+'/datasetselectwidget/datasetselectwidget.js'),
  DatasetWidget:require(__dirname+'/datasetwidget/datasetwidget.js'),
  LariLoginWidget:require(__dirname+'/lariloginwidget/lariloginwidget.js'),
};

window.render_widget=function(widget_name,props,element) {
	const Index = function(props) {
	  return <div>Title: {props.title}</div>;
	};
	let C=registered_widgets[widget_name];
	if (!C) {
		console.error('No such widget: '+widget_name);
		return;
	}
	//console.log(C);
	//ReactDOM.render(React.createElement('Index',props), element[0]);
	//ReactDOM.render(<Index title={props.title} />, element[0]);
	//ReactDOM.render(React.createElement(Index,props), element[0]);
	return ReactDOM.render(React.createElement(C,props), element[0]);
};
*/

window.TimeseriesModel=require(__dirname+'/ephys_viz/timeseriesmodel.js').TimeseriesModel;
window.TimeseriesWidget=require(__dirname+'/ephys_viz/timeserieswidget.js').TimeseriesWidget;
window.GeomWidget=require(__dirname+'/ephys_viz/geomwidget.js').GeomWidget;
window.Mda=require(__dirname+'/ephys_viz/mda.js').Mda;
window.test_ephys_viz=function(div_id) {
	let X=new window.Mda(4,1000);
	let TS=new window.TimeseriesModel(X);
	let W=new window.TimeseriesWidget();
	W.setTimeseriesModel(TS);
	W.setSize(800,400);
	$('#'+div_id).append(W.div());
}


