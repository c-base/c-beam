
function formatDate(date) {
  var day = date.getDate()
  if (day < 10) {
    day = '0' + day
  }
  var month = date.getMonth() + 1
  if (month < 10) {
    month = '0' + month
  }
  var year = date.getFullYear()
  if (year < 10) {
    year = '0' + year
  }
  return year + '-' + month + '-' + day
}

function formatTime(date) {
  var hh = date.getHours()
  if (hh < 10) {
    hh = '0' + hh
  }
  var min = date.getMinutes()
  if (min < 10) {
    min = '0' + min
  }
  return hh + ':' + min
}

function formatDateTime(date) {
  return formatDate(date) + ' ' + formatTime(date);
}

module.exports = {
  formatDate,
  formatDateTime,
  formatTime
}



