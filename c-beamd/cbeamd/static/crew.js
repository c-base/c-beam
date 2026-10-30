// keeps the crew list (#crew-list on / and /user/online) current: once a
// minute the list is fetched from its partial view and swapped in, but only
// when it changed, so that open panels stay open and nothing flickers while
// nobody comes or goes. the terminal below is untouched by this.
(function () {
  'use strict';

  var list = document.getElementById('crew-list');
  if (!list || !list.dataset.url) { return; }

  var INTERVAL = 60000;
  var last = null;   // the html last received; the first fetch replaces unconditionally

  function openPanels() {
    return Array.prototype.map.call(list.querySelectorAll('.panel-collapse.in'), function (el) { return el.id; });
  }

  function swap(html) {
    var open = openPanels();
    list.innerHTML = html;
    open.forEach(function (id) {
      var el = document.getElementById(id);
      if (el) { el.classList.add('in'); }
    });
  }

  function refresh() {
    if (document.hidden) { return; }   // a background tab need not poll
    fetch(list.dataset.url, { credentials: 'same-origin', headers: { 'X-Requested-With': 'fetch' } })
      .then(function (response) {
        if (!response.ok) { throw new Error(response.status); }
        return response.text();
      })
      .then(function (html) {
        if (html !== last) {
          last = html;
          swap(html);
        }
      })
      .catch(function () { /* next minute, then */ });
  }

  window.setInterval(refresh, INTERVAL);
  document.addEventListener('visibilitychange', function () { if (!document.hidden) { refresh(); } });
})();
