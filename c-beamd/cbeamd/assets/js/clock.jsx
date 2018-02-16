const JQuery = require('jquery');
const React = require('react');
import {formatDateTime} from "./utils/date";

const updateInterval = 10000;

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
    super(props)
    this.state = {time: "time is being created..."}
    this.update = this.update.bind(this)
  }
  update() {
    this.setState({time: formatDateTime(new Date())})
  }

  componentDidMount() {
    this.update() // do it once and then start it up ...
    this._timer = setInterval(this.update, updateInterval)
  }
  componentWillUnmount() {
    if (this._timer) {
      clearInterval(this._timer);
      this._timer = null;
    }
  }
  render() {
    return  (
      <div>
        <div className="clock-display">{this.state.time}</div>
      </div>
    )
  }
}

module.exports = ClockWidget;

