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

  // what was sent before, for arrow up and down like in a shell; kept per tab
  var HISTORY_KEY = 'assistant.history';
  var HISTORY_MAX = 50;
  var history = [];
  var position = 0;      // index into history while browsing, history.length otherwise
  var draft = '';        // what was typed before browsing started

  try { history = JSON.parse(sessionStorage.getItem(HISTORY_KEY) || '[]'); } catch (e) { history = []; }
  if (!Array.isArray(history)) { history = []; }
  position = history.length;

  function recordInput(text) {
    if (history[history.length - 1] !== text) {
      history.push(text);
      if (history.length > HISTORY_MAX) { history.shift(); }
      try { sessionStorage.setItem(HISTORY_KEY, JSON.stringify(history)); } catch (e) { /* no storage */ }
    }
    position = history.length;
    draft = '';
  }

  function browse(step) {
    if (!history.length) { return; }
    if (position === history.length) { draft = input.value; }
    position = Math.max(0, Math.min(history.length, position + step));
    input.value = position === history.length ? draft : history[position];
    // the cursor goes to the end, where it is when a line was just typed
    var end = input.value.length;
    window.setTimeout(function () { input.setSelectionRange(end, end); }, 0);
  }

  input.addEventListener('keydown', function (event) {
    if (event.key === 'Enter') {
      event.preventDefault();
      var text = input.value.trim();
      input.value = '';
      if (text) { recordInput(text); }
      ask(text, false);
    } else if (event.key === 'ArrowUp') {
      event.preventDefault();
      browse(-1);
    } else if (event.key === 'ArrowDown') {
      event.preventDefault();
      browse(1);
    }
  });

  // a click anywhere in the box puts the cursor on the prompt line, like a
  // terminal, unless the click was the end of a text selection: focusing
  // would throw the selection away before it can be copied
  box.addEventListener('click', function (event) {
    if (event.target.tagName === 'BUTTON' || busy || !configured) { return; }
    var selection = window.getSelection ? window.getSelection() : null;
    if (selection && selection.toString()) { return; }
    input.focus();
  });

  if (configured) { input.focus(); }
  scroll();
})();

// reading answers aloud (AI-ASSISTANT.md, section 10), in the browser with
// speechSynthesis: optional, off by default, and only with a german voice
// that runs on the device, so that no answer goes to a cloud service. the
// station's names are english words a german voice would spell out; they are
// swapped for phonetic spellings before speaking.
(function () {
  'use strict';

  var Assistant = window.cbeamAssistant;
  var toggle = document.getElementById('assistant-speak');
  var box = document.getElementById('assistant');
  if (!Assistant || !toggle || !box) { return; }

  var STORAGE_KEY = 'assistant.speak';
  // chosen by ear for the voices at hand; check again when they change
  var PRONUNCIATION = [
    [/\bc-base\b/gi, 'ssiebays'],
    [/\bc-beam\b/gi, 'ssiebiem'],
    [/\bcrew\b/gi, 'kru']
  ];

  var synth = window.speechSynthesis;
  var available = !!(synth && window.SpeechSynthesisUtterance);
  var warned = false;

  function remember(on) {
    try { localStorage.setItem(STORAGE_KEY, on ? '1' : '0'); } catch (e) { /* private window etc. */ }
  }

  function remembered() {
    try { return localStorage.getItem(STORAGE_KEY) === '1'; } catch (e) { return false; }
  }

  function notice(text) {
    var el = document.createElement('div');
    el.className = 'line-info';
    el.textContent = text;
    box.insertBefore(el, document.getElementById('assistant-line'));
    box.scrollTop = box.scrollHeight;
  }

  // a german voice on the device; voices load late in some browsers, so this
  // is looked up at speaking time, not once at start
  function germanVoice() {
    var voices = synth.getVoices() || [];
    var german = voices.filter(function (v) { return /^de(-|_|$)/i.test(v.lang); });
    var local = german.filter(function (v) { return v.localService; });
    if (local.length) {
      var exact = local.filter(function (v) { return /^de[-_]DE$/i.test(v.lang); });
      return exact[0] || local[0];
    }
    return null;
  }

  function pronounce(text) {
    PRONUNCIATION.forEach(function (pair) { text = text.replace(pair[0], pair[1]); });
    return text;
  }

  function silence() {
    if (available) { synth.cancel(); }
  }

  function say(text) {
    if (!available || !toggle.checked || !text) { return; }
    var voice = germanVoice();
    if (!voice) {
      if (!warned) {
        warned = true;
        notice('sprachausgabe: keine deutsche offline-stimme im browser');
      }
      return;
    }
    silence();
    var utterance = new SpeechSynthesisUtterance(pronounce(text));
    utterance.voice = voice;
    utterance.lang = voice.lang;
    utterance.rate = 1;
    synth.speak(utterance);
  }

  if (!available) {
    toggle.disabled = true;
    toggle.parentNode.title = 'der browser hat keine sprachausgabe';
  } else {
    toggle.checked = remembered();
    if (synth.getVoices && synth.addEventListener) {
      synth.addEventListener('voiceschanged', function () { /* warms the voice list */ });
    }
  }

  toggle.addEventListener('change', function () {
    remember(toggle.checked);
    if (!toggle.checked) { silence(); }
  });

  // what the server marked for speaking: the answer, "Erledigt." after a
  // self action, "<beschreibung>. Ausführen?" for a proposal
  Assistant.hooks.reply.push(function (reply) { say(reply.speak); });

  // nothing keeps talking after the page is gone, and nothing is spoken into
  // a recording (block 8 calls silence() before it starts)
  window.addEventListener('pagehide', silence);
  Assistant.silence = silence;
  Assistant.say = say;
})();
