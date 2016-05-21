const JQuery = require('jquery');
const React = require('react');
const ReactDOM = require('react-dom');

function formatDate(d) {
  var dd = d.getDate()
  var mm = d.getMonth()+1
  if ( mm < 10 ) mm = '0' + mm
  var yy = d.getFullYear()
  if ( yy < 10 ) yy = '0' + yy
  var hh = d.getHours()
  if ( hh < 10 ) hh = '0' + hh
  var min = d.getMinutes()
  if ( min < 10 ) min = '0' + min
  return yy+'-'+mm+'-'+dd+'T'+hh+':'+min
}

var ClockWidget = React.createClass({
  componentDidMount: function() {
    this.startUpdating();
  },

  componentWillUnmount: function() {
    if (this._timer) {
      clearInterval(this._timer);
      this._timer = null;
    }
  },
  getInitialState: function() {
    return {data: {time: "time is being created..."}};
  },
  startUpdating: function() {
    var self = this;
    if (!self.isMounted()) { return; } // abandon
    self.update(); // do it once and then start it up ...
    self._timer = setInterval(self.update, 10000); //this.props.pollInterval);
  },

  update: function() {
    //this.setState({data: {time: new Date().toLocaleString().slice(0, -3)}});
    this.setState({data: {time: formatDate(new Date())}});
  },

  render: function() {
    return  (
      <div>
        <div className="clock-display">{this.state.data.time}</div>
      </div>
    )
  }

});

module.exports = ClockWidget;
