const React = require('react');
const ReactDOM = require('react-dom/client');

const BarStatus = require('./barstatus');
const ClockWidget = require('./clock');
const MpdWidget = require('./mpdwidget');

// react 18 replaced ReactDOM.render with createRoot; a missing container is no
// longer silently ignored, so each mount point is checked first — the two
// widgets live on different pages.
function mount(elementId, element) {
  const container = document.getElementById(elementId);
  if (container) {
    ReactDOM.createRoot(container).render(element);
  }
}

//mount('mpd', <BarStatus />);
mount('clock', <ClockWidget updateInterval={1000} />);
mount('mpd', <MpdWidget pollInterval={1000} host={window.mpdHostname} />);
