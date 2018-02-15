const jQuery = require('jquery');
const React = require('react');
const PropTypes = require('prop-types')
const _ = require('lodash');

jQuery.DataTable = require("datatables.net-bs");
require('datatables.net-buttons/js/buttons.colVis.js');
require('datatables.net-buttons/js/buttons.print.js');
require("datatables.net-buttons-bs");
require("datatables.net-responsive-bs");
require("datatables.net-select");

import 'datatables.net-bs/css/dataTables.bootstrap.css';
import 'datatables.net-buttons-bs/css/buttons.bootstrap.css';
import 'datatables.net-select-bs/css/select.bootstrap.css';

const updateInterval = 1000

function Column(props) {
  return <th>{props.text}</th>
}
Column.propTypes = {
  text: PropTypes.string.isRequired
}

class DataTable extends React.Component {
  constructor(props, context) {
    super(props, context);
    this.update = this.update.bind(this);
  }
  update() {
    //console.log("update", this.props.data)
    let datatable = jQuery('#'+this.props.tableId).DataTable()
    datatable.clear();
    datatable.rows.add(this.props.data);
    datatable.draw();
    //console.log("update done")
  }
  componentDidMount() {
    let defaultConfig = {
      colReorder: true,
      searching: false,
      paging:  true,
      pagingType: "simple_numbers",
      //"scrollY":        "20ve",
      //"scrollCollapse": true,
      lengthChange: false,
      autoWidth: false,
      responsive: true,
      dom: "<'row'<'col-sm-12'lB>>" +
          "<'row'<'col-sm-12'tr>>" +
          "<'row'<'col-sm-5'i><'col-sm-7'p>>",
      columns: this.props.columns,
    }
    let config = $.extend(
        { },
        defaultConfig,
        this.props.options
      )
    if (this.props.hasOwnProperty('url')) {
      jQuery('#'+this.props.tableId).DataTable({
        ...config,
        ajax: {
          url: this.props.url,
          dataSrc: this.props.dataSrc,
          error: (xhr, status, err) => {
            console.error(this.props.url, status, err.toString());
          }
        }
      })
    } else if (this.props.hasOwnProperty('data')) {
      jQuery('#'+this.props.tableId).DataTable({
        ...config,
        data: this.props.data
      })
    }
    if (this.props.data) {
      //this._timer = setInterval(this.update, updateInterval)
    }
  }
  shouldComponentUpdate(nextProps, nextState) {
    if (!_.isMatch(this.props.data, nextProps.data)) {
      console.log("update", this.props.data, nextProps.data)

      this._timer = setTimeout(this.update, updateInterval)
      //this.update()
    }
    //return !_.isMatch(this.props.data, nextProps.data)
    return false
  }
  render() {
    console.log("render")
    let columns = this.props.columns.map((column, i) => <Column text={column.title} key={this.props.tableId + i} />);
    return  (
      <div className="table-responsive">
        <table id={this.props.tableId} className="table table-hover display" style={{width: "100%"}}>
          <thead>
            <tr>
              {columns}
            </tr>
          </thead>
          <tbody>
          </tbody>
        </table>
      </div>
    )
  }
}
DataTable.propTypes = {
  tableId: PropTypes.string.isRequired,
  columns: PropTypes.array.isRequired,
  options: PropTypes.object,
  url: PropTypes.string,
  dataSrc: PropTypes.string,  // https://datatables.net/reference/option/ajax.dataSrc
  data: PropTypes.array,
}



module.exports = DataTable;
