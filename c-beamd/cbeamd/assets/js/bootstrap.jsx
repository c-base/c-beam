const React = require('react');
const PropTypes = require('prop-types');

class BootstrapPanel extends React.Component {
  render() {
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
}

BootstrapPanel.propTypes = {
  title: PropTypes.node,
  body: PropTypes.node,
};

module.exports = {
      panel: BootstrapPanel,
}
