var JQuery = require('jquery');
//window.jQuery = $;
//window.$ = $;

var React = require('react');
var ReactDOM = require('react-dom');

var BarStatus = require('./barstatus');
var ClockWidget = require('./clock');
var MpdWidget = require('./mpdwidget');

ReactDOM.render(<BarStatus />, document.getElementById('mpd'));
ReactDOM.render(<ClockWidget />, document.getElementById('clock'));
//ReactDOM.render(<MpdWidget />, document.getElementById('mpd'));
