var JQuery = require('jquery');
//window.jQuery = $;
//window.$ = $;

var React = require('react');
var ReactDOM = require('react-dom');

var BarStatus = require('./barstatus');
var ClockWidget = require('./clock');
var MpdWidget = require('./mpdjs');
//var MpdWidget = require('./mpdwidget');

//ReactDOM.render(<BarStatus />, document.getElementById('mpd'));
ReactDOM.render(<ClockWidget updateInterval={1000} />, document.getElementById('clock'));
ReactDOM.render(<MpdWidget pollInterval={1000} url={window.mpdUrl} />, document.getElementById('mpd'));
