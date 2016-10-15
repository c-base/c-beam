const JQuery = require('jquery');
const React = require('react');
const ReactDOM = require('react-dom');

const class_closed = "btn btn-block btn-danger";
const class_open = "btn btn-block btn-success";
var BarStatus = React.createClass({
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
    return {data: {barstatus: 'bar closed', barstatus_class: class_closed}};
  },
  startUpdating: function() {
    var self = this;
    if (!self.isMounted()) { return; } // abandon
    self.update(); // do it once and then start it up ...
    self._timer = setInterval(self.update, 10000); //this.props.pollInterval);
  },

  update: function() {
    this.setState({data: {barstatus: 'bar closed', barstatus_class: class_closed}});
  },

  render: function() {
    return  (
      <div id="barstatus">
        <div className={this.state.data.barstatus_class}>{this.state.data.barstatus}</div>
      </div>
    )
  }

});

module.exports = BarStatus;
