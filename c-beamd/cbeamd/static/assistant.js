// the terminal of /assistant (AI-ASSISTANT.md, section 11), in plain
// javascript: a prompt line that sends on enter, the answer lines the server
// returns, progress lines that the next output replaces rather than follows,
// and the two buttons of a confirmation. the browser only talks to c-beam.
//
// speaking (block 7) and the microphone (block 8) hook in through
// Assistant.hooks.reply and Assistant.ask.

(function () {
  'use strict';

  var box = document.getElementById('assistant');
  if (!box) { return; }

  var input = document.getElementById('assistant-input');
  var inputLine = document.getElementById('assistant-line');   // stays the last line of the box
  var askUrl = box.dataset.askUrl;
  var confirmUrl = box.dataset.confirmUrl;
  var username = box.dataset.username;
  var configured = box.dataset.configured === '1';

  var MAX_LINES = 200;
  var busy = false;
  var progress = null;   // the progress line, replaced by the next output
  var buttons = null;    // the buttons of the open proposal

  var Assistant = {
    hooks: { reply: [] },   // fn(reply) after every answer, e.g. to speak it
    ask: ask,
    busy: function () { return busy; }
  };
  window.cbeamAssistant = Assistant;

  // the terminal -----------------------------------------------------------------

  function scroll() {
    box.scrollTop = box.scrollHeight;
  }

  function trim() {
    while (box.children.length > MAX_LINES + 1) {
      box.removeChild(box.firstChild);
    }
  }

  // every output goes in above the prompt line, which stays at the bottom
  function append(el) {
    box.insertBefore(el, inputLine);
    trim();
    scroll();
    return el;
  }

  // the kind is prefixed: bootstrap owns names like .progress (a progress bar)
  function line(kind, text) {
    var el = document.createElement('div');
    el.className = 'line-' + kind;
    el.textContent = text;
    return append(el);
  }

  function promptLine(text) {
    var el = document.createElement('div');
    var prompt = document.createElement('span');
    prompt.className = 'prompt';
    prompt.textContent = username + '@c-beam>';
    el.appendChild(prompt);
    el.appendChild(document.createTextNode(' ' + text));
    return append(el);
  }

  function setProgress(text) {
    if (progress) {
      progress.textContent = text;
    } else {
      progress = line('progress', text);
    }
    scroll();
  }

  function clearProgress() {
    if (progress && progress.parentNode) {
      progress.parentNode.removeChild(progress);
    }
    progress = null;
  }

  function dropButtons() {
    if (buttons && buttons.parentNode) {
      buttons.parentNode.removeChild(buttons);
    }
    buttons = null;
  }

  function confirmButtons(proposal) {
    var el = document.createElement('div');
    el.className = 'line-buttons';
    var reject = document.createElement('button');
    reject.type = 'button';
    reject.className = 'btn btn-default btn-xs';
    reject.textContent = 'verwerfen';
    var accept = document.createElement('button');
    accept.type = 'button';
    accept.className = 'btn btn-primary btn-xs';
    accept.textContent = 'ausführen';
    reject.addEventListener('click', function () { decide(proposal.id, false); });
    accept.addEventListener('click', function () { decide(proposal.id, true); });
    el.appendChild(reject);
    el.appendChild(accept);
    return append(el);
  }

  function show(reply) {
    clearProgress();
    (reply.lines || []).forEach(function (entry) {
      line(entry.kind, entry.text);
    });
    if (reply.confirm) {
      buttons = confirmButtons(reply.confirm);
    }
    Assistant.hooks.reply.forEach(function (hook) {
      try { hook(reply); } catch (e) { console.error(e); }
    });
  }

  // talking to c-beam -------------------------------------------------------------

  function csrfToken() {
    var match = document.cookie.match(/(?:^|;\s*)csrftoken=([^;]+)/);
    return match ? decodeURIComponent(match[1]) : '';
  }

  function post(url, body) {
    return fetch(url, {
      method: 'POST',
      credentials: 'same-origin',
      headers: { 'Content-Type': 'application/json', 'X-CSRFToken': csrfToken() },
      body: JSON.stringify(body)
    }).then(function (response) {
      return response.json().catch(function () {
        throw new Error('server antwortet nicht (' + response.status + ')');
      });
    }).catch(function (error) {
      return { lines: [{ kind: 'error', text: 'fehler: ' + (error.message || 'keine verbindung zu c-beam') }] };
    });
  }

  function setBusy(value) {
    busy = value;
    input.disabled = value || !configured;
    if (!value && configured) { input.focus(); }
  }

  function ask(text, voice) {
    text = (text || '').trim();
    if (!text || busy || !configured) { return; }
    dropButtons();   // a new request rejects the open proposal; the server records that
    setBusy(true);
    promptLine(text);
    setProgress('denke nach…');
    post(askUrl, { text: text, voice: !!voice }).then(function (reply) {
      show(reply);
      setBusy(false);
    });
  }

  function decide(id, accept) {
    if (busy) { return; }
    dropButtons();
    setBusy(true);
    setProgress(accept ? 'fu:hre aus…' : 'verwerfe…');
    post(confirmUrl, { id: id, accept: accept }).then(function (reply) {
      show(reply);
      setBusy(false);
    });
  }

  // the prompt line ---------------------------------------------------------------

  input.addEventListener('keydown', function (event) {
    if (event.key === 'Enter') {
      event.preventDefault();
      var text = input.value;
      input.value = '';
      ask(text, false);
    }
  });

  // a click anywhere in the box puts the cursor on the prompt line, like a terminal
  box.addEventListener('click', function (event) {
    if (event.target.tagName !== 'BUTTON' && !busy && configured) { input.focus(); }
  });

  if (configured) { input.focus(); }
  scroll();
})();
