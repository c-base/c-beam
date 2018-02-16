const JQuery = require('jquery');
const React = require('react');

const class_closed = "btn btn-block btn-danger";
const class_open = "btn btn-block btn-success";

class BarStatus extends React.Component {
  componentDidMount() {
    this.startUpdating();
  }

  componentWillUnmount() {
    if (this._timer) {
      clearInterval(this._timer);
      this._timer = null;
    }
  }

  getInitialState() {
    return {data: {barstatus: 'bar closed', barstatus_class: class_closed}};
  }

  startUpdating() {
    var self = this;
    if (!self.isMounted()) { return; } // abandon
    self.update(); // do it once and then start it up ...
    self._timer = setInterval(self.update, 10000); //this.props.pollInterval);
  }

  update() {
    this.setState({data: {barstatus: 'bar closed', barstatus_class: class_closed}});
  }

  render() {
    return  (
      <div id="barstatus">
        <div className={this.state.data.barstatus_class}>{this.state.data.barstatus}</div>
      </div>
    )
  }

}

module.exports = BarStatus;
