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
    busy: function () { return busy; },
    // for the other sections of this file
    line: null, append: null, progress: null, clearProgress: null, recordInput: null, csrfToken: null
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

  // the model choice, kept in the session by the server
  var modelSelect = document.getElementById('assistant-model');
  if (modelSelect && box.dataset.modelUrl) {
    modelSelect.addEventListener('change', function () {
      post(box.dataset.modelUrl, { model: modelSelect.value }).then(show);
    });
  }

  // typing anywhere on the page goes to the prompt line, like in a terminal
  // window; focusing it then scrolls the terminal into view. form fields and
  // shortcuts with modifiers keep their keys
  document.addEventListener('keydown', function (event) {
    if (document.activeElement === input || busy || !configured) { return; }
    var tag = (event.target.tagName || '').toLowerCase();
    if (tag === 'input' || tag === 'textarea' || tag === 'select' || event.target.isContentEditable) { return; }
    if (event.ctrlKey || event.altKey || event.metaKey) { return; }
    if (event.key.length === 1 || event.key === 'ArrowUp' || event.key === 'Backspace') {
      input.focus();
    }
  });

  Assistant.line = line;
  Assistant.append = append;
  Assistant.progress = setProgress;
  Assistant.clearProgress = clearProgress;
  Assistant.recordInput = recordInput;
  Assistant.csrfToken = csrfToken;

  // the cursor starts on the prompt line only when the terminal is already in
  // view (as on /assistant); on the start page it sits below the crew list,
  // and focusing it there would scroll the whole page down on every load
  if (configured && box.getBoundingClientRect().top < window.innerHeight) { input.focus(); }
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

  // a german voice, preferably one on the device; voices load late in some
  // browsers, so this is looked up at speaking time, not once at start
  function pick(voices) {
    var exact = voices.filter(function (v) { return /^de[-_]DE$/i.test(v.lang); });
    return exact[0] || voices[0] || null;
  }

  function germanVoice() {
    var voices = synth.getVoices() || [];
    var german = voices.filter(function (v) { return /^de(-|_|$)/i.test(v.lang); });
    var local = german.filter(function (v) { return v.localService; });
    if (local.length) { return pick(local); }
    // only a voice of the browser's provider: the answer text leaves the
    // device for it, which is why the app does not do this; said once
    var online = pick(german);
    if (online && !warned) {
      warned = true;
      notice('sprachausgabe: keine offline-stimme, nutze „' + online.name + '“; der text geht dafu:r an den browser-anbieter');
    }
    return online;
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
        notice('sprachausgabe: der browser hat keine deutsche stimme');
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

// hold to talk (AI-ASSISTANT.md, sections 3 and 4): the microphone runs only
// while the button is held, visibly, with no wake word. the samples are
// recorded through an audio worklet, written as a 16 kHz mono 16 bit wav and
// sent to c-beam, which hands them to whisper; the transcript then goes the
// same way as a typed line. needs https or localhost for getUserMedia.
(function () {
  'use strict';

  var Assistant = window.cbeamAssistant;
  var box = document.getElementById('assistant');
  var button = document.getElementById('assistant-mic');
  var note = document.getElementById('assistant-mic-note');
  var bar = document.getElementById('assistant-record');
  var timeEl = document.getElementById('assistant-time');
  var levelEl = document.getElementById('assistant-level');
  if (!Assistant || !box || !button || !bar) { return; }

  var transcribeUrl = box.dataset.transcribeUrl;
  var workletUrl = box.dataset.workletUrl;
  var configured = box.dataset.configured === '1';

  var RATE = 16000;          // what whisper wants; more brings nothing
  var MAX_SECONDS = 20;      // hard limit, then the recording sends itself
  var MIN_SECONDS = 0.5;     // shorter was a tap, not speech

  var supported = !!(navigator.mediaDevices && navigator.mediaDevices.getUserMedia &&
                     window.AudioContext && window.isSecureContext);
  if (!configured) { return; }
  if (!supported) {
    if (note) { note.style.display = ''; }
    return;
  }
  button.style.display = '';

  var recording = null;   // {context, stream, node, blocks, started, outside}

  // before the first recording, and so before the browser asks for the
  // microphone, the same notice as in the android app; the first press shows
  // it instead of recording, the next one records
  var NOTICE_KEY = 'assistant.mic.notice';
  var NOTICE = 'die aufnahme la:uft nur, solange der knopf gehalten wird. sie geht zum ' +
               'KI-server der station, der nur im crew-netz erreichbar ist, und wird dort in ' +
               'text umgewandelt. c-beam speichert nichts davon.';
  var noticeShown = false;

  function noticeAcknowledged() {
    try { return localStorage.getItem(NOTICE_KEY) === '1'; } catch (e) { return noticeShown; }
  }

  function showNotice() {
    if (noticeShown) { return; }
    noticeShown = true;
    Assistant.line('info', 'mikrofon: ' + NOTICE);
    var el = document.createElement('div');
    el.className = 'line-buttons';
    var ok = document.createElement('button');
    ok.type = 'button';
    ok.className = 'btn btn-primary btn-xs';
    ok.textContent = 'verstanden';
    ok.addEventListener('click', function () {
      try { localStorage.setItem(NOTICE_KEY, '1'); } catch (e) { /* kept for this page only */ }
      el.parentNode.removeChild(el);
      Assistant.line('info', 'mikrofon: knopf halten und sprechen');
    });
    el.appendChild(ok);
    Assistant.append(el);
  }

  function formatTime(seconds) {
    seconds = Math.floor(seconds);
    return Math.floor(seconds / 60) + ':' + ('0' + (seconds % 60)).slice(-2);
  }

  function showBar(on) {
    bar.classList.toggle('active', on);
    bar.classList.remove('cancel');
    button.classList.toggle('recording', on);
    if (!on) { levelEl.style.width = '0'; }
  }

  function updateMeter(block, elapsed) {
    var sum = 0;
    for (var i = 0; i < block.length; i++) { sum += block[i] * block[i]; }
    var rms = Math.sqrt(sum / (block.length || 1));
    levelEl.style.width = Math.min(200, Math.round(rms * 600)) + 'px';
    timeEl.textContent = formatTime(elapsed) + ' / ' + formatTime(MAX_SECONDS);
  }

  // float32 at the context's rate -> int16 at RATE, linear interpolation
  function toPcm16(blocks, fromRate) {
    var total = 0;
    blocks.forEach(function (b) { total += b.length; });
    var samples = new Float32Array(total);
    var offset = 0;
    blocks.forEach(function (b) { samples.set(b, offset); offset += b.length; });
    var ratio = fromRate / RATE;
    var length = Math.floor(samples.length / ratio);
    var pcm = new Int16Array(length);
    for (var i = 0; i < length; i++) {
      var pos = i * ratio;
      var left = Math.floor(pos);
      var right = Math.min(left + 1, samples.length - 1);
      var value = samples[left] + (samples[right] - samples[left]) * (pos - left);
      value = Math.max(-1, Math.min(1, value));
      pcm[i] = value < 0 ? value * 0x8000 : value * 0x7FFF;
    }
    return pcm;
  }

  function wav(pcm) {
    var buffer = new ArrayBuffer(44 + pcm.length * 2);
    var view = new DataView(buffer);
    function str(at, text) { for (var i = 0; i < text.length; i++) { view.setUint8(at + i, text.charCodeAt(i)); } }
    str(0, 'RIFF'); view.setUint32(4, 36 + pcm.length * 2, true); str(8, 'WAVE');
    str(12, 'fmt '); view.setUint32(16, 16, true); view.setUint16(20, 1, true); view.setUint16(22, 1, true);
    view.setUint32(24, RATE, true); view.setUint32(28, RATE * 2, true); view.setUint16(32, 2, true); view.setUint16(34, 16, true);
    str(36, 'data'); view.setUint32(40, pcm.length * 2, true);
    new Int16Array(buffer, 44).set(pcm);
    return new Blob([buffer], { type: 'audio/wav' });
  }

  function start() {
    if (recording || Assistant.busy()) { return; }
    if (!noticeAcknowledged()) { showNotice(); return; }
    if (Assistant.silence) { Assistant.silence(); }   // never record the station's own voice
    var rec = { blocks: [], started: 0, outside: false, context: null, stream: null, node: null };
    recording = rec;
    navigator.mediaDevices.getUserMedia({ audio: { channelCount: 1, echoCancellation: true, noiseSuppression: true } })
      .then(function (stream) {
        if (recording !== rec) { stream.getTracks().forEach(function (t) { t.stop(); }); return; }
        rec.stream = stream;
        var context;
        try { context = new AudioContext({ sampleRate: RATE }); } catch (e) { context = new AudioContext(); }
        rec.context = context;
        return context.audioWorklet.addModule(workletUrl).then(function () {
          if (recording !== rec) { return; }
          var source = context.createMediaStreamSource(stream);
          var node = new AudioWorkletNode(context, 'assistant-recorder');
          rec.node = node;
          rec.started = Date.now();
          node.port.onmessage = function (event) {
            if (recording !== rec) { return; }
            rec.blocks.push(event.data);
            var elapsed = (Date.now() - rec.started) / 1000;
            updateMeter(event.data, elapsed);
            if (elapsed >= MAX_SECONDS) { stop(false); }
          };
          source.connect(node);
          node.connect(context.destination);   // keeps the graph alive; the node emits silence
          showBar(true);
          timeEl.textContent = '0:00 / ' + formatTime(MAX_SECONDS);
        });
      })
      .catch(function (error) {
        recording = null;
        showBar(false);
        Assistant.line('error', 'fehler: mikrofon nicht verfügbar (' + (error.name || error) + ')');
      });
  }

  function release(rec) {
    if (rec.node) { rec.node.port.onmessage = null; rec.node.disconnect(); }
    if (rec.stream) { rec.stream.getTracks().forEach(function (t) { t.stop(); }); }
    if (rec.context) { rec.context.close().catch(function () {}); }
  }

  function stop(cancelled) {
    var rec = recording;
    if (!rec) { return; }
    recording = null;
    showBar(false);
    try {
      release(rec);
      if (!rec.started) { return; }
      if (cancelled) {
        Assistant.line('info', 'aufnahme verworfen');
        return;
      }
      var seconds = (Date.now() - rec.started) / 1000;
      if (seconds < MIN_SECONDS) {
        Assistant.line('info', 'zum sprechen halten');
        return;
      }
      if (!rec.blocks.length) {
        Assistant.line('error', 'fehler: keine audiodaten vom mikrofon');
        return;
      }
      send(wav(toPcm16(rec.blocks, rec.context.sampleRate)));
    } catch (error) {
      console.error(error);
      Assistant.line('error', 'fehler: aufnahme konnte nicht verarbeitet werden (' + (error.message || error) + ')');
    }
  }

  function send(blob) {
    var form = new FormData();
    form.append('file', blob, 'speech.wav');
    Assistant.progress('transkribiere…');
    fetch(transcribeUrl, {
      method: 'POST',
      credentials: 'same-origin',
      headers: { 'X-CSRFToken': Assistant.csrfToken() },
      body: form
    }).then(function (response) {
      return response.json().catch(function () { throw new Error('server antwortet nicht (' + response.status + ')'); });
    }).then(function (data) {
      Assistant.clearProgress();
      if (data.error || !data.text) {
        Assistant.line('error', 'fehler: ' + (data.error || 'nichts verstanden'));
        return;
      }
      Assistant.recordInput(data.text);
      Assistant.ask(data.text, true);
    }).catch(function (error) {
      Assistant.clearProgress();
      Assistant.line('error', 'fehler: ' + (error.message || 'keine verbindung zu c-beam'));
    });
  }

  // the button: pointer events cover mouse, touch and pen. moving off the
  // button and letting go there discards the recording, like in the app
  button.addEventListener('pointerdown', function (event) {
    event.preventDefault();
    button.setPointerCapture(event.pointerId);
    start();
  });
  // whether the pointer has left the button is tracked while it moves; the
  // coordinates of the release itself are not trusted (they are not reliable
  // under pointer capture in every browser)
  button.addEventListener('pointerup', function (event) {
    event.preventDefault();
    stop(!!(recording && recording.outside));
  });
  button.addEventListener('pointermove', function (event) {
    if (!recording) { return; }
    var rect = button.getBoundingClientRect();
    var margin = 24;
    var outside = event.clientX < rect.left - margin || event.clientX > rect.right + margin ||
                  event.clientY < rect.top - margin || event.clientY > rect.bottom + margin;
    recording.outside = outside;
    bar.classList.toggle('cancel', outside);
    if (outside) { timeEl.textContent = 'loslassen zum verwerfen'; }
  });
  button.addEventListener('pointercancel', function () { stop(true); });
  button.addEventListener('contextmenu', function (event) { event.preventDefault(); });
  window.addEventListener('pagehide', function () { stop(true); });
})();
