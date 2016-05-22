const JQuery = require('jquery');
const React = require('react');
const ReactDOM = require('react-dom');
//const FancyTree = require('jquery.fancytree');
const createFragment = require('react-addons-create-fragment');
const BootstrapPanel = require('./bootstrap').panel;

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

var MpdStatus = React.createClass({
  //update: function(event) {
    //this.setState({status: jQuery.get("/mpd/status/")});
  //},
  render: function() {
    var title = "";
    var artist = "";
    var album = "";
    if (this.props.data.current_song != null) {
        title = this.props.data.current_song.title;
        artist = this.props.data.current_song.artist;
        album = this.props.data.current_song.album;
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
      </div>
    )
  }

});

var MpdVolButton = React.createClass({
  propTypes: {
    command: React.PropTypes.string.isRequired,
    host: React.PropTypes.string.isRequired,
  },
  handleClick: function(event) {
    jQuery.get('/mpd/'+this.props.host+'/command/' + this.props.command + '/')
  },
  render: function() {
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
});

var MpdControlButton = React.createClass({
  propTypes: {
    command: React.PropTypes.string.isRequired,
    host: React.PropTypes.string.isRequired,
  },
  handleClick: function(event) {
    jQuery.get('/mpd/'+this.props.host+'/command/' + this.props.command + '/')
  },
  render: function() {
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
});


var MpdVolumeControl = React.createClass({
  propTypes: {
  },
  contextTypes: {
    volume: React.PropTypes.number
  },
  handleChange: function(event) {
    //var volume = this.refs.mpd_volume;
    //console.log('set volume to' + volume.value)
    //jQuery.get('/mpd/command/' + this.props.command + '/')
    this.setState({data: {volume: event.target.value}});
  },
  getInitialState: function() {
    return {data: {volume: 0}};
  },
  render: function() {
          //<input id="mpd_volume" className="slider" type="range" min="0" max="100" step="5" onChange={this.handleChange} ref="mpd_volume" value={this.props.data.volume} />
    return  (
      <div className="col-md-4 column btn-group btn-group-lg volumecontrol">
          <MpdVolButton command="vol_down" host="mechblast" />
          <input id="mpd_volume" className="slider" type="range" min="0" max="100" step="5" onChange={this.handleChange} ref="mpd_volume" value={this.props.data.volume} />
          <MpdVolButton command="vol_up" host="mechblast" />
      </div>
    )
  }
});

var MpdControls = React.createClass({
  propTypes: {
  },
  render: function() {
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
});

var MpdPlaybackPosition = React.createClass({
  propTypes: {
  },
  contextTypes: {
    position: React.PropTypes.number,
    elapsed: React.PropTypes.number,
    total: React.PropTypes.number
  },
  handleChange: function(event) {
    this.setState({data: {position: event.target.value}});
  },
  getInitialState: function() {
    return {data: {position: 0, elapsed: 0, total: 0}};
  },
  render: function() {
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
});

var MpdWidget = React.createClass({
  childContextTypes: {
    volume: React.PropTypes.number
  },
  getStatus: function() {
    jQuery.ajax({
      url: "/mpd/"+this.props.host+"/status/",
      dataType: 'json',
      cache: false,
      success: function(data) {
        this.setState({data: data});
      }.bind(this),
      error: function(xhr, status, err) {
        console.error(this.props.url, status, err.toString());
      }.bind(this)
    });
  },
  //getChildContext: function() {
    //return {volume: this.state.data.content.state.volume};
  //},
  propTypes: {
    //url: React.PropTypes.string.isRequired,
  },
  getInitialState: function() {
    return {data: {content: {state: "unknown", volume: 0, elapsed: 0, total: 0}}};
  },
  componentDidMount: function() {
    var self = this;
    this.getStatus();
    setInterval(this.getStatus, this.props.pollInterval);
  },
  render: function() {
    return  (
      <div className="mpd-widget">
        <MpdStatus data={this.state.data.content} />
        <MpdControls />
        <div className="row mpdcontrol">
          <MpdPlaybackPosition data={this.state.data.content} />
          <MpdVolumeControl data={this.state.data.content} />
        </div>
      </div>
    )
  }
});



//
//module.exports = {
      //panel: FancyTreeWidget,
//}

module.exports = MpdWidget;
