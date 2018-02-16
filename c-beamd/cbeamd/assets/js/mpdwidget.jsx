const JQuery = require('jquery');
const React = require('react');
const ReactDOM = require('react-dom');
//const FancyTree = require('jquery.fancytree');
const createFragment = require('react-addons-create-fragment');
const BootstrapPanel = require('./bootstrap').panel;
const PropTypes = require('prop-types')

String.prototype.toHHMMSS = function () {
    var sec_num = parseInt(this, 10); // don't forget the second param
    var hours   = Math.floor(sec_num / 3600);
    var minutes = Math.floor((sec_num - (hours * 3600)) / 60);
    var seconds = sec_num - (hours * 3600) - (minutes * 60);

    if (hours   < 10) {hours   = "0"+hours;}
    if (minutes < 10) {minutes = "0"+minutes;}
    if (seconds < 10) {seconds = "0"+seconds;}
    var time    = hours+':'+minutes+':'+seconds;
    return time;
}

class MpdStatus extends React.Component {
  render() {
    var title = "";
    var artist = "";
    var album = "";
    var elapsed = "--:--:--";
    var total = "--:--:--";
    if (this.props.data.current_song != null) {
        title = this.props.data.current_song.title;
        artist = this.props.data.current_song.artist;
        album = this.props.data.current_song.album;
        elapsed = String(this.props.data.elapsed).toHHMMSS();
        total = String(this.props.data.total).toHHMMSS();
    }
    var random = "fa fa-random";
    if (this.props.data.random == 0) {
        random += " disabled";
    }
    var repeat = "fa fa-repeat";
    if (this.props.data.repeat == 0) {
        repeat += " disabled";
    }
    var state = "fa fa-question";
    if (this.props.data.state == "play") {
        state = "fa fa-play";
    } else if (this.props.data.state == "pause") {
        state = "fa fa-pause";
    } else if (this.props.data.state == "stop") {
        state = "fa fa-stop";
    }
    //<div>Single: {this.props.data.single}</div>
    return  (
      <div className="mpdstatus row">
        <div className="column col-md-11">
          <div className="songinfo">Title: {title}</div>
          <div>Artist: {artist}</div>
          <div>Album: {album}</div>
        </div>
        <div className="column col-md-1 right">
          <div><i className={state}></i></div>
          <div><i className={random}></i></div>
          <div><i className={repeat}></i></div>
        </div>
        <div className="column col-md-12">
          <div>Position: {elapsed}&#47;{total}</div>
        </div>
      </div>
    )
  }
}

class MpdVolButton extends React.Component {
  propTypes: {
    command: React.PropTypes.string.isRequired,
    host: React.PropTypes.string.isRequired,
  }
  handleClick(event) {
    jQuery.get('/mpd/'+this.props.host+'/command/' + this.props.command + '/')
  }
  render() {
    var label = "fa fa-question";
    if (this.props.command == 'vol_up') {
      label = "fa fa-plus";
    } else if (this.props.command == 'vol_down') {
      label = "fa fa-minus";
    }
    return  (
      <a onClick={this.handleClick} className="btn btn-default btn-vol"><i className={label}></i></a>
    )
  }
}

class MpdControlButton extends React.Component {
  constructor(props) {
    super(props)
    this.handleClick = this.handleClick.bind(this)
  }
  handleClick(event) {
    jQuery.get('/mpd/'+this.props.host+'/command/' + this.props.command + '/')
  }
  render() {
    var label = "fa fa-question";
    if (this.props.command == 'play') {
      label = "fa fa-play";
    } else if (this.props.command == 'pause') {
      label = "fa fa-pause";
    } else if (this.props.command == 'stop') {
      label = "fa fa-stop";
    } else if (this.props.command == 'next') {
      label = "fa fa-step-forward";
    } else if (this.props.command == 'previous') {
      label = "fa fa-step-backward";
    } else if (this.props.command == 'playlists') {
      label = "fa fa-list";
    } else if (this.props.command == 'random') {
      label = "fa fa-random";
    } else if (this.props.command == 'repeat') {
      label = "fa fa-repeat";
    } else if (this.props.command == 'forward') {
      label = "fa fa-forward";
    } else if (this.props.command == 'backward') {
      label = "fa fa-backward";
    }
    return  (
      <a onClick={this.handleClick} className="btn btn-default"><i className={label}></i></a>
    )
  }
}
MpdControlButton.propTypes = {
  command: PropTypes.string.isRequired,
  host: PropTypes.string.isRequired,
}


class MpdVolumeControl extends React.Component {
  constructor(props) {
    super(props)
    this.state = {volume: 0}
    this.handleChange = this.handleChange.bind(this)
  }
  handleChange(event) {
    this.setState({data: {volume: event.target.value}});
  }
  getInitialState() {
    return {data: {volume: 0}};
  }
  render() {
    return  (
      <div className="col-md-4 column btn-group btn-group-lg volumecontrol">
          <MpdVolButton command="vol_down" host="mechblast" />
          <input id="mpd_volume" className="slider" type="range" min="0" max="100" step="5" onChange={this.handleChange} ref="mpd_volume" value={this.props.data.volume} />
          <MpdVolButton command="vol_up" host="mechblast" />
      </div>
    )
  }
}
MpdVolumeControl.propTypes =  {
  volume: PropTypes.number.isRequired
}

class MpdControls extends React.Component {
  constructor(props) {
    super(props)
  }
  render() {
    return  (
      <div className="row">
        <div className="btn-group btn-group-justified btn-group-lg">
          <MpdControlButton command="previous" host='mechblast' />
          <MpdControlButton command="backward" host='mechblast' />
          <MpdControlButton command="stop" host='mechblast' />
          <MpdControlButton command="play" host='mechblast' />
          <MpdControlButton command="pause" host='mechblast' />
          <MpdControlButton command="forward" host='mechblast' />
          <MpdControlButton command="next" host='mechblast' />
          <MpdControlButton command="playlists" host='mechblast' />
          <MpdControlButton command="random" host='mechblast' />
          <MpdControlButton command="repeat" host='mechblast' />
        </div>
      </div>
    )
  }
}

class MpdPlaybackPosition extends React.Component {
  constructor(props) {
    super(props)
    this.state = {'data': {elapsed: ''}}

    this.handleChange = this.handleChange.bind(this)
  }
  handleChange(event) {
    this.setState({data: {position: event.target.value}});
  }
  getInitialState() {
    return {data: {position: 0, elapsed: 0, total: 0}};
  }
  render() {
    // 'time': '364:4535'
    return  (
      <div className="column col-md-8">
          <input id="mpd_playback_position" className="slider" type="range" min="0" max={this.props.data.total} step="5" onChange={this.handleChange} ref="mpd_playback_position" value={this.props.data.elapsed} />
          <table className="position-display" width="100%">
              <tbody>
              <tr>
                  <td>0:00</td>
                  <td className="center">{String(this.props.data.elapsed).toHHMMSS()}</td>
                  <td className="right">{String(this.props.data.total).toHHMMSS()}</td>
              </tr>
              </tbody>
          </table>
      </div>
    )
  }
}
MpdPlaybackPosition.propTypes = {
  elapsed: PropTypes.number.isRequired,
  total: PropTypes.number.isRequired,
  position: PropTypes.object,
}

class MpdWidget extends React.Component {
  constructor(props) {
    super(props)
    this.state = {data: {content: {state: "unknown", volume: 0, elapsed: 0, total: 0}, host: 'mechblast' }};
    this.getStatus = this.getStatus.bind(this)
  }
  getStatus() {
    var self = this
    console.log(this.props.host)
    jQuery.ajax({
      url: "/mpd/"+this.props.host+"/status/",
      dataType: 'json',
      cache: false,
      success(data) {
        self.setState({data: data});
      },
      error(xhr, status, err) {
        console.error(self.props.host, status, err.toString());
      }
    });
  }
  componentDidMount() {
    var self = this;
    this.getStatus();
    setInterval(this.getStatus, this.props.pollInterval);
  }
  render() {
        //<MpdControls />
        //<div className="row mpdcontrol">
          //<MpdPlaybackPosition data={this.state.data.content} />
          //<MpdVolumeControl data={this.state.data.content} />
        //</div>
    return  (
      <div className="mpd-widget">
        <MpdStatus data={this.state.data.content} />
      </div>
    )
  }
}

MpdWidget.propTypes = {
  url: PropTypes.string,
  host: PropTypes.string,
}


//
//module.exports = {
      //panel: FancyTreeWidget,
//}

module.exports = MpdWidget;
