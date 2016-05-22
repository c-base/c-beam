var JQuery = require('jquery');
var React = require('react');

var BootstrapPanel = React.createClass({
  render: function() {
    return (
      <div className="panel panel-default">
        <div className="panel-heading">
          {this.props.title}
        </div>
        <div className="panel-body">
          {this.props.body}
        </div>
      </div>
    );
  }
})

module.exports = {
      panel: BootstrapPanel,
}
