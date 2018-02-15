const jQuery = require('jquery')
const React = require('react')
const {Tabs, Tab} = require('react-bootstrap')
const PropTypes = require('prop-types')
const DataTable = require('./utils/datatable')
const MPC = require('mpc-js-web').MPC;
const strftime = require('strftime')

//require('../css/mpd.css')

let MPD_WEBSOCKET_URL = 'ws://10.0.1.23:6601/'

String.prototype.toHHMMSS = function () {
    let sec_num = parseInt(this, 10) // don't forget the second param
    let hours   = Math.floor(sec_num / 3600)
    let minutes = Math.floor((sec_num - (hours * 3600)) / 60)
    let seconds = sec_num - (hours * 3600) - (minutes * 60)

    if (hours   < 10) {hours   = "0"+hours}
    if (minutes < 10) {minutes = "0"+minutes}
    if (seconds < 10) {seconds = "0"+seconds}
    return hours+':'+minutes+':'+seconds
}

class MpdStatus extends React.Component {
  render() {
    let currentSong = {
      title: "",
      artist: "",
      album: "",
      elapsed: "--:--:--",
      duration: "--:--:--",
    }
    if (this.props.currentSong) {
      currentSong = this.props.currentSong
    }
    currentSong.elapsed = String(this.props.mpdstatus.elapsed).toHHMMSS();
    currentSong.total = String(this.props.currentSong.duration).toHHMMSS();
    let random = "fa fa-random"
    if (this.props.mpdstatus.random == 0) {
      random += " disabled"
    }
    let repeat = "fa fa-repeat"
    if (this.props.mpdstatus.repeat == 0) {
      repeat += " disabled"
    }
    let state = "fa fa-question"
    if (this.props.mpdstatus.state === "play") {
      state = "fa fa-play"
    } else if (this.props.mpdstatus.state === "pause") {
      state = "fa fa-pause"
    } else if (this.props.mpdstatus.state === "stop") {
      state = "fa fa-stop"
    }
    return  (
      <div className="mpdstatus row">
        <div className="column col-md-11">
          <div className="songinfo">Title: {currentSong.title}</div>
          <div>Artist: {currentSong.artist}</div>
          <div>Album: {currentSong.album}</div>
        </div>
        <div className="column col-md-1 right">
          <div><i className={state}></i></div>
          <div><i className={random}></i></div>
          <div><i className={repeat}></i></div>
        </div>
        <div className="column col-md-12">
          <div>Position: {currentSong.elapsed}&#47;{currentSong.total}</div>
        </div>
      </div>
    )
  }
}
MpdStatus.propTypes = {
  current_song: PropTypes.object,
  random: PropTypes.string,
  repeat: PropTypes.string,
  state: PropTypes.string,
}

class MpdVolButton extends React.Component {
  constructor(props) {
    super(props)
    this.handleClick = this.handleClick.bind(this)
  }
  handleClick() {
    this.props.execCommand(this.props.command)
    //jQuery.get('/mpd/command/' + this.props.command + '/')
  }
  render() {
    let label = "fa fa-question"
    if (this.props.command === 'vol_up') {
      label = "fa fa-plus"
    } else if (this.props.command === 'vol_down') {
      label = "fa fa-minus"
    }
    return  (
      <a onClick={this.handleClick} className="btn btn-default btn-vol"><i className={label} /></a>
    )
  }
}
MpdVolButton.propTypes = {
  command: PropTypes.string.isRequired
}

class MpdControlButton extends React.Component {
  constructor(props) {
    super(props)
    this.handleClick = this.handleClick.bind(this)
  }
  handleClick() {
    if (this.props.command === 'playlists') {
      this.props.switchTab()
    } else {
      this.props.execCommand(this.props.command)
      //jQuery.get('/mpd/command/' + this.props.command + '/')
    }
  }
  render() {
    let label = "fa fa-question"
    if (this.props.command === 'play') {
      label = "fa fa-play"
    } else if (this.props.command === 'pause') {
      label = "fa fa-pause"
    } else if (this.props.command === 'stop') {
      label = "fa fa-stop"
    } else if (this.props.command === 'next') {
      label = "fa fa-step-forward"
    } else if (this.props.command === 'previous') {
      label = "fa fa-step-backward"
    } else if (this.props.command === 'playlists') {
      label = "fa fa-list"
    } else if (this.props.command === 'random') {
      label = "fa fa-random"
    } else if (this.props.command === 'repeat') {
      label = "fa fa-repeat"
    } else if (this.props.command === 'forward') {
      label = "fa fa-forward"
    } else if (this.props.command === 'backward') {
      label = "fa fa-backward"
    }
    return (
      <a onClick={this.handleClick} className="btn btn-default"><i className={label} /></a>
    )
  }
}
MpdControlButton.propTypes = {
  command: PropTypes.string.isRequired,
}


class MpdVolumeControl extends React.Component {
  constructor(props) {
    super(props)
    this.state = {volume: 0}
    this.handleChange = this.handleChange.bind(this)
  }

  handleChange(event) {
    this.setState({volume: event.target.value})
    this.props.mpc.playbackOptions.setVolume(event.target.value, false)
  }

  render() {
    return  (
      <div className="btn-group btn-group-lg volumecontrol col-md-4 column">
          <MpdVolButton command="vol_down" execCommand={this.props.execCommand} />
          <input id="mpd_volume" className="slider" type="range" min="0" max="100" step="5" onChange={this.handleChange} ref="mpd_volume" value={this.props.volume} />
          <MpdVolButton command="vol_up" execCommand={this.props.execCommand} />
      </div>
    )
  }
}
MpdVolumeControl.propTypes =  {
  volume: PropTypes.number.isRequired
}


//function MpdControls(props) {
class MpdControls extends React.Component {
  constructor(props) {
    super(props)
  }

  render() {
    return  (
      <div className="row">
        <div className="btn-group btn-group-justified btn-group-lg">
          <MpdControlButton command="previous" execCommand={this.props.execCommand} />
          <MpdControlButton command="backward" execCommand={this.props.execCommand} />
          <MpdControlButton command="stop" execCommand={this.props.execCommand} />
          <MpdControlButton command="play" execCommand={this.props.execCommand} />
          <MpdControlButton command="pause" execCommand={this.props.execCommand} />
          <MpdControlButton command="forward" execCommand={this.props.execCommand} />
          <MpdControlButton command="next" execCommand={this.props.execCommand} />
          <MpdControlButton command="playlists" switchTab={this.props.switchTab} />
          <MpdControlButton command="random" execCommand={this.props.execCommand} />
          <MpdControlButton command="repeat" execCommand={this.props.execCommand} />
        </div>
      </div>
    )
  }
}

class MpdPlaybackPosition extends React.Component {
  constructor(props) {
    super(props)
    this.state = {elapsed: ''}

    this.handleChange = this.handleChange.bind(this)
  }

  handleChange(event) {
    this.setState({elapsed: event.target.value})
    this.props.mpc.playback.seekCur(event.target.value, false)
  }

  render() {
    return  (
      <div className="column col-md-8">
        <input id="mpd_playback_position"
               className="slider"
               type="range" min="0" max={this.props.duration} step="5"
               onChange={this.handleChange}
               ref="mpd_playback_position" value={this.props.elapsed} />
        <table className="position-display" width="100%">
          <tbody>
          <tr>
            <td>0:00</td>
            <td className="center">{String(this.props.elapsed).toHHMMSS()}</td>
            <td className="right">{String(this.props.duration).toHHMMSS()}</td>
          </tr>
          </tbody>
        </table>
      </div>
    )
  }
}
MpdPlaybackPosition.propTypes = {
  elapsed: PropTypes.number.isRequired,
  duration: PropTypes.number.isRequired,
  mpc: PropTypes.object,
}

class MpdPlaylist extends React.Component {
  constructor(props) {
    super(props)
    //this.state = {playlist: []}
  }
  render() {
    let table_id = "mpd-table"
    let columns = [
      { title: "#", data: "position", defaultContent: "" },
      { title: "Title", defaultContent: "" },
      { title: "Artist", data: "artist", defaultContent: "" },
      //{ title: "Album", data: "album", defaultContent: "" },
      //{ title: "Length", data: "length", defaultContent: "" },
    ]
    let mpc = this.props.mpc
    let datatableOptions = {
      select: {
        style:    'multi+shift',
      },
      "columnDefs": [
        {
          "targets": 1,
          "data": function ( row, type, val, meta ) {
            return row.title || row.name || row.path;
          }
        },
      ],
      buttons: [
        { extend: 'selectAll', className: 'btn-lg' },
        { extend: 'selectNone', className: 'btn-lg' },
        {
          text: '<i class="fa fa-chevron-up" />',
          className: 'btn-lg',
          action: function ( e, dt, node, config ) {
            console.log("up", $('#'+table_id).DataTable().rows( { selected: true } ).data().toArray())
          }
        },
        {
          text: '<i class="fa fa-chevron-down" />',
          className: 'btn-lg',
          action: function ( e, dt, node, config ) {
            console.log("down", $('#'+table_id).DataTable().rows( { selected: true } ).data().toArray())
          }
        },
        {
          text: '<i class="fa fa-play" />',
          className: 'btn-lg',
          action: function ( e, dt, node, config ) {
            let table = $('#'+table_id).DataTable()
            let selected = table.rows( { selected: true } ).data().toArray()
            mpc.playback.playId(selected[0].id)
          }
        },
        {
          text: '<i class="fa fa-trash" />',
          className: 'btn-lg',
          action: function ( e, dt, node, config ) {
            let table = $('#'+table_id).DataTable()
            let selected = table.rows( { selected: true } ).data().toArray()
            for (var i=0; i < selected.length; i++) {
              mpc.currentPlaylist.deleteId(selected[i].id)
            }
          }
        },
        {
          text: '<i class="fa fa-save" />',
          className: 'btn-lg',
          action: function ( e, dt, node, config ) {
            let table = $('#'+table_id).DataTable()
            let name = strftime("%Y-%m-%d_%H:%M")
            mpc.storedPlaylists.save(name)
          }
        }
      ]
    }
    return (
      <div className='terminal'>
        <DataTable tableId={table_id} className="mpd-playlist" options={datatableOptions} columns={columns} data={this.props.playlist} />
      </div>
    )
  }
}
MpdPlaylist.propTypes = {
  playlist: PropTypes.array.isRequired,
  mpc: PropTypes.object.isRequired,
}

class MpdPlaylistSelector extends React.Component {
  render() {
    let table_id = "mpd-playlist-selector"
    let mpc = this.props.mpc
    let columns = [
      { title: "Name", data: "name", defaultContent: "" },
      { title: "Last modified", data: "lastModified", defaultContent: "" },
      //{ title: "Append", data: null, defaultContent: "<button class='btn btn-default btn-large'>Append</a>" },
      //{ title: "Replace", data: null, defaultContent: "<button class='btn btn-default btn-large'>Replace</button>" }
    ]
    let datatableOptions = {
      select: 'single',
      buttons: [
        {
          text: 'Append',
          className: 'btn-lg',
          action: function ( e, dt, node, config ) {
            let table = $('#'+table_id).DataTable()
            let selected = table.rows( { selected: true } ).data().toArray()
            mpc.storedPlaylists.load(selected[0].playlist)
          }
        },
        {
          text: 'Replace',
          className: 'btn-lg',
          action: function ( e, dt, node, config ) {
            let table = $('#'+table_id).DataTable()
            let selected = table.rows( { selected: true } ).data().toArray()
            mpc.currentPlaylist.clear()
            mpc.storedPlaylists.load(selected[0].playlist)
          },
        },
        {
          text: '<i class="fa fa-trash" />',
          className: 'btn-lg',
          action: function ( e, dt, node, config ) {
            let table = $('#'+table_id).DataTable()
            let selected = table.rows( { selected: true } ).data().toArray()
            mpc.storedPlaylists.remove(selected[0].playlist)
          }
        },
      ],
    }
    return  (
      <div className='terminal' >
        <DataTable tableId={table_id} className="mpd-playlist" options={datatableOptions} columns={columns} data={this.props.listOfPlaylists} />
      </div>
    )
  }
}
MpdPlaylistSelector.propTypes = {
  mpc: PropTypes.object.isRequired,
}


class MpdTabs extends React.Component {
  constructor(props, context) {
    super(props, context);
    this.handleSelect = this.handleSelect.bind(this);
  }

  handleSelect(tab) {
    this.setState({ tab });
  }

  render() {
    return (
      <Tabs
        activeKey={this.props.tab}
        onSelect={this.handleSelect}
        animation={false}
        id="controlled-tab-example"
      >
        <Tab eventKey={1} tabClassName={'hidden'} title="current playlist">
          <MpdPlaylist playlist={this.props.playlist} mpc={this.props.mpc} />
        </Tab>
        <Tab eventKey={2} tabClassName={'hidden'} title="playlists">
          <MpdPlaylistSelector {...this.props} mpc={this.props.mpc} />
        </Tab>
      </Tabs>
    );
  }
}
MpdTabs.propTypes = {
  tab: PropTypes.number.isRequired,
  mpc: PropTypes.object.isRequired,
}

class MpdWidget extends React.Component {
  constructor(props) {
    super(props)
    this.defaultCurrentSong = {title: "- No active track -", duration: 0}
    this.defaultMpdstatus = {state: "unknown", random: 0, repeat: 0, volume: 0, elapsed: 0}
    this.mpc = new MPC()
    this.mpc.connectWebSocket(this.props.url || MPD_WEBSOCKET_URL).then(result => {
      // TODO handle connection error
      this.update()
      setInterval(this.update, this.props.pollInterval)
    });
    this.state = {
      playlist: [],
      listOfPlaylists: [],
      tab: 1,
      currentSong: this.defaultCurrentSong,
      mpdstatus: this.defaultMpdstatus,
    }
    this.update = this.update.bind(this)
    this.execCommand = this.execCommand.bind(this)
    this.switchTab = this.switchTab.bind(this)
  }

  update() {
    this.mpc.status.status()
    .then(status => { 
      if (isNaN(status.elapsed)) { status.elapsed = 0 }
      this.mpc.status.currentSong()
      .then(currentSong => {
        if (currentSong && isNaN(currentSong.duration)) { currentSong.duration = 0 }
        this.mpc.currentPlaylist.playlistInfo()
        .then(playlist => {
          this.mpc.storedPlaylists.listPlaylists()
          .then(listOfPlaylists => {
            this.setState({
              mpdstatus: status || this.defaultMpdstatus,
              currentSong: currentSong || this.defaultCurrentSong,
              playlist: playlist || [],
              listOfPlaylists: listOfPlaylists || [],
            });
          });
        });
      });
    });
  }

  execCommand(command) {
    if (command === 'play') {
      this.mpc.playback.play()
    } else if (command === 'pause') {
      this.mpc.playback.pause()
    } else if (command === 'stop') {
      this.mpc.playback.stop()
    } else if (command === 'next') {
      this.mpc.playback.next()
    } else if (command === 'previous') {
      this.mpc.playback.previous()
    } else if (command === 'random') {
      this.mpc.playbackOptions.setRandom(!this.state.mpdstatus.random)
    } else if (command === 'repeat') {
      this.mpc.playbackOptions.setRepeat(!this.state.mpdstatus.repeat)
    } else if (command === 'forward') {
      this.mpc.playback.seekCur(10.0, true)
    } else if (command === 'backward') {
      this.mpc.playback.seekCur(-10.0, true)
    } else if (command === 'vol_up') {
      this.mpc.playbackOptions.setVolume(this.state.mpdstatus.volume + 5)
    } else if (command === 'vol_down') {
      this.mpc.playbackOptions.setVolume(this.state.mpdstatus.volume - 5)
    }
  }

  switchTab() {
    if (this.state.tab == 1) {
      this.setState({tab: 2})
    } else {
      this.setState({tab: 1})
    }
  }

  componentDidMount() {
    //this.update()
    //setInterval(this.update, this.props.pollInterval)
  }
/*
*/
  render() {
    console.log(this.state)
    /*
        <MpdControls switchTab={this.switchTab} execCommand={this.execCommand} />
        <div className="row mpdcontrol">
          <MpdPlaybackPosition elapsed={this.state.mpdstatus.elapsed} duration={this.state.currentSong.duration} mpc={this.mpc}  />
          <MpdVolumeControl volume={this.state.mpdstatus.volume} execCommand={this.execCommand} mpc={this.mpc} />
        </div>
        <MpdTabs {...this.state} mpc={this.mpc} />
    */
    return  (
      <div className="mpd-widget">
        <MpdStatus {...this.state} />
      </div>
    )
  }
}

MpdWidget.propTypes = {
  url: PropTypes.string,
}

module.exports = MpdWidget
