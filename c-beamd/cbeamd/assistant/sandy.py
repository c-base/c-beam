"""
sandy strands as a knowledge source (AI-ASSISTANT.md, section 9.2): the
station's experimental voice assistant with a rag of its own. sandy answers
the question completely, with sources; our model then makes its answer out of
that, which keeps the station tools with our model.

sandy only speaks over its voice websocket, one connection per question:

1. open the socket (5 s). no ping/pong watchdog: sandy takes longer than the
   default interval.
2. set_voice de, or sandy answers in english whatever the question's language.
3. send the question as text_input.
4. read frames until a bot_text with done: true arrives (typically 10 to 15 s,
   at most 90). binary frames are sandy's voice as raw pcm and are dropped;
   the browser speaks our model's answer itself.
"""

import json
import logging
import time

import cbeamdcfg as cfg

from .chat import AssistantError

# websocket-client is imported when sandy is asked, not here: this module is
# reached through the url configuration of every page, and a missing optional
# dependency must not take the whole site down with it
try:
    from websocket import ABNF, WebSocketException, WebSocketTimeoutException, create_connection
except ImportError:   # pragma: no cover - exercised in a subprocess test
    ABNF = WebSocketException = WebSocketTimeoutException = create_connection = None

logger = logging.getLogger(__name__)

CONNECT_TIMEOUT = 5
ANSWER_TIMEOUT = 90
MAX_CHARS = 1500

HEADER = ("Antwort des Stations-Assistenten Sandy Strands auf die Suchanfrage „%s“. Sie ist die "
          "Fundstelle: die Fakten daraus verwenden, Sandys Rückfragen und Höflichkeiten weglassen, "
          "nichts hinzuerfinden:")
NOTHING = ("nichts gefunden: sandy strands hat zu „%s“ nichts gesagt. sage das und verweise auf die "
           "datenrettungssonde siri, die diese information leider auch nicht enthält")


def available():
    """whether websocket-client is installed."""
    return create_connection is not None


def configured():
    return bool(cfg.sandy_url) and available()


def _sources(entries):
    """the source names out of sandy's [{"src": …} or {"path": …}], in order, once each."""
    names = []
    for entry in entries or []:
        if isinstance(entry, dict):
            name = entry.get('src') or entry.get('path') or entry.get('source')
        else:
            name = entry
        name = ' '.join(str(name or '').split())
        if name and name not in names:
            names.append(name)
    return names


def format_answer(question, text, sources):
    text = ' '.join((text or '').split())
    if not text:
        return NOTHING % question
    if len(text) > MAX_CHARS:
        text = text[:MAX_CHARS - 1].rstrip() + '…'
    result = HEADER % question + '\n\n' + text
    names = _sources(sources)
    if names:
        result += '\n\nQuellen: ' + ', '.join(names)
    return result


def converse(ws, question):
    """
    the (text, sources) of sandy's final answer on an open socket, or
    AssistantError. sandy's sentence-wise bot_text frames are skipped; only the
    one with done: true carries the whole text.
    """
    ws.send(json.dumps({'type': 'control', 'action': 'set_voice', 'voice': 'de'}))
    ws.send(json.dumps({'type': 'text_input', 'text': question}))
    deadline = time.monotonic() + ANSWER_TIMEOUT
    while True:
        remaining = deadline - time.monotonic()
        if remaining <= 0:
            raise AssistantError("sandy strands antwortet nicht")
        ws.settimeout(remaining)
        try:
            opcode, data = ws.recv_data()
        except WebSocketTimeoutException:
            raise AssistantError("sandy strands antwortet nicht")
        if opcode == ABNF.OPCODE_CLOSE:
            return None, []
        if opcode != ABNF.OPCODE_TEXT:
            continue   # binary: sandy's voice, dropped
        try:
            frame = json.loads(data)
        except ValueError:
            continue
        if not isinstance(frame, dict):
            continue
        kind = frame.get('type')
        if kind == 'bot_text' and frame.get('done'):
            return frame.get('text'), frame.get('sources') or []
        if kind == 'error':
            raise AssistantError("sandy strands: %s" % ' '.join(str(frame.get('message') or 'fehler').split()))
        # bot_text without done, tool_log, sys_log: progress only


def ask(question):
    """the tool result of station_knowledge for question, from sandy."""
    if not available():
        raise AssistantError("sandy strands: websocket-client ist nicht installiert")
    if not configured():
        raise AssistantError("sandy strands nicht konfiguriert")
    try:
        ws = create_connection(cfg.sandy_url, timeout=CONNECT_TIMEOUT)
    except (WebSocketException, OSError) as e:
        logger.warning("sandy connection failed: %s", e)
        raise AssistantError("sandy strands nicht erreichbar")
    try:
        text, sources = converse(ws, question)
    except (WebSocketException, OSError) as e:
        logger.warning("sandy conversation failed: %s", e)
        raise AssistantError("sandy strands: verbindung abgebrochen")
    finally:
        try:
            ws.close()
        except Exception:
            pass
    return format_answer(question, text, sources)
