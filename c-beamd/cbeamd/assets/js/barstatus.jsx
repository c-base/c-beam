const React = require('react');

const class_closed = "btn btn-block btn-danger";
const class_open = "btn btn-block btn-success";

class BarStatus extends React.Component {
  constructor(props) {
    super(props);
    this.state = {data: {barstatus: 'bar closed', barstatus_class: class_closed}};
    this._timer = null;
    this.update = this.update.bind(this);
  }

  componentDidMount() {
    this.startUpdating();
  }

  componentWillUnmount() {
    if (this._timer) {
      clearInterval(this._timer);
      this._timer = null;
    }
  }

  startUpdating() {
    this.update(); // do it once and then start it up ...
    this._timer = setInterval(this.update, 10000); //this.props.pollInterval);
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
