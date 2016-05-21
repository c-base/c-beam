const JQuery = require('jquery');
const React = require('react');
const ReactDOM = require('react-dom');

var komponist = require('komponist')

var MpdWidget = React.createClass({
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
    var songinfo = null;
    komponist.createConnection(function(err, client) {
        client.currentsong(function(err, info) {
            songinfo = info;
            console.log(info.Artist); // Ennio Morricone
            console.log(info.Title);  // Il Buono, Il Cattivo, Il Brutto
            console.log(info.Album);  // The Good, The Bad, And The Ugly
        });
    });
    //this.setState({data: {time: new Date().toLocaleString().slice(0, -3)}});
    this.setState({data: {title: 'foo'}});
  },

  render: function() {
    return  (
      <div>
        <div>{this.state.data.title}</div>
      </div>
    )
  }

});

module.exports = MpdWidget;
