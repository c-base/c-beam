const React = require('react');

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

class ClockWidget extends React.Component {
  constructor(props) {
    super(props);
    this.state = {data: {time: "time is being created..."}};
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
    //this.setState({data: {time: new Date().toLocaleString().slice(0, -3)}});
    this.setState({data: {time: formatDate(new Date())}});
  }

  render() {
    return  (
      <div>
        <div className="clock-display">{this.state.data.time}</div>
      </div>
    )
  }
}

module.exports = ClockWidget;
