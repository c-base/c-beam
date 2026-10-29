"""
http to the station's ai server, done the way the android app does it
(AI-ASSISTANT.md, sections 5 and 13): an openai-compatible endpoint behind
which a small model with tool calling answers, plus the workarounds its quirks
need. this module only moves bytes; what the tools do and how the conversation
is kept live next door.

errors are raised as AssistantError with the text the terminal shows after
"fehler: ", so the views need no mapping of their own.
"""

import json
import logging
import re
import time
import uuid
from dataclasses import dataclass, field
from typing import Optional

import requests

import cbeamdcfg as cfg

logger = logging.getLogger(__name__)

# enough for three spoken sentences without cutting a free answer short
MAX_TOKENS = 400
# a 429 whose Retry-After is longer than this is reported instead of waited out
MAX_RETRY_AFTER = 5

BUSY = "KI-server ausgelastet"
NOTHING_HEARD = "nichts verstanden"
# whisper's prompt is not an instruction but a spelling aid: it pulls the
# recognition towards these words. without it "c-base" came out as "Seabase"
# or "Siebe" and "Crew-WLAN" as "QWLAN"
WHISPER_PROMPT = ("c-base, c-beam, Crew-WLAN, c-lab, Matelight, Club-Mate, Bordcomputer, Artefakt, "
                  "Mission, Durchsage, Raumstation.")
WHISPER_READ_TIMEOUT = 30
NOT_UNDERSTOOD = "nicht verstanden"
UNREADABLE = "KI-server: unlesbare antwort"

# a tool call the model wrote as text instead of as a tool_call, e.g.
# station_knowledge(query="wlan passwort"); arguments are key="…" or key='…'
_TEXT_CALL = re.compile(r'^\s*([a-z_]+)\((.*)\)\s*$', re.DOTALL)
_TEXT_ARG = re.compile(r'''\s*([a-z_]+)\s*=\s*(?:"([^"]*)"|'([^']*)')\s*(?:,|$)''')


class AssistantError(Exception):
    """a failure with a message for the terminal (without the "fehler: " prefix)."""


@dataclass
class ToolCall:
    name: str
    arguments: dict
    id: str = field(default_factory=lambda: 'call_' + uuid.uuid4().hex[:8])

    def message(self):
        """the assistant message that records this call in the conversation."""
        return {
            'role': 'assistant',
            'content': None,
            'tool_calls': [{
                'id': self.id,
                'type': 'function',
                'function': {
                    'name': self.name,
                    'arguments': json.dumps(self.arguments, ensure_ascii=False),
                },
            }],
        }


@dataclass
class ModelReply:
    """what one round gave back: either words or (the first) tool call."""
    text: Optional[str] = None
    tool_call: Optional[ToolCall] = None


def configured():
    return bool(cfg.ai_url)


def _url(path):
    return cfg.ai_url.rstrip('/') + '/' + path.lstrip('/')


def _retry_after(response):
    """the Retry-After header in seconds, or None when missing or not a number."""
    value = response.headers.get('Retry-After')
    try:
        return int(value)
    except (TypeError, ValueError):
        return None


def post(path, *, json=None, data=None, files=None, read_timeout=None):
    """
    POST to the ai server and return the decoded json body.

    the server limits bursts with a 429 and a Retry-After of a second or two;
    that is waited out once. a longer Retry-After, a second 429, timeouts and
    http errors become AssistantErrors.
    """
    return _send('POST', path, json=json, data=data, files=files, read_timeout=read_timeout)


def get(path, read_timeout=None):
    return _send('GET', path, read_timeout=read_timeout)


def _send(method, path, *, json=None, data=None, files=None, read_timeout=None):
    if not configured():
        raise AssistantError("KI-server nicht konfiguriert")
    timeout = (cfg.ai_connect_timeout, read_timeout or cfg.ai_read_timeout)
    waited = False
    while True:
        try:
            response = requests.request(method, _url(path), json=json, data=data, files=files, timeout=timeout)
        except requests.Timeout:
            raise AssistantError("KI-server antwortet nicht")
        except requests.RequestException as e:
            logger.warning("ai server request failed: %s", e)
            raise AssistantError("KI-server nicht erreichbar")
        if response.status_code == 429:
            retry_after = _retry_after(response)
            if retry_after is not None and retry_after <= MAX_RETRY_AFTER and not waited:
                time.sleep(retry_after)
                waited = True
                continue
            if retry_after:
                raise AssistantError("%s, in %d s nochmal" % (BUSY, retry_after))
            raise AssistantError(BUSY)
        if not response.ok:
            logger.warning("ai server answered %s: %s", response.status_code, response.text[:200])
            raise AssistantError("KI-server: HTTP %d" % response.status_code)
        try:
            return response.json()
        except ValueError:
            raise AssistantError(UNREADABLE)


# the model list, cached per process: it changes when someone loads a model
# on the server, not between two page views
MODELS_TTL = 300
_models_cache = (0.0, [])


def models():
    """
    [{'id', 'labels'}] of the chat models on the ai server, from GET /models.
    embedding models (label embeddings, or "embed" in the name) are left out;
    labels like tool-calling, coding or vision are kept as hints. empty when
    the server cannot be asked.
    """
    global _models_cache
    fetched, found = _models_cache
    now = time.monotonic()
    if now - fetched < MODELS_TTL:
        return found
    found = []
    try:
        for entry in (get('models', read_timeout=10) or {}).get('data') or []:
            model_id = entry.get('id') if isinstance(entry, dict) else None
            if not isinstance(model_id, str) or not model_id:
                continue
            labels = [str(label) for label in entry.get('labels') or [] if label]
            if 'embeddings' in labels or 'embed' in model_id.lower():
                continue
            found.append({'id': model_id, 'labels': labels})
    except AssistantError as e:
        logger.warning("model list unavailable: %s", e)
    _models_cache = (now, found)
    return found


def reset_models():
    global _models_cache
    _models_cache = (0.0, [])


def parse_text_tool_call(text, names):
    """
    a ToolCall when text looks exactly like name(key="value", …) and name is one
    of names, else None. gemma writes about one call in ten this way; left
    alone, the call would be read out to the user.
    """
    m = _TEXT_CALL.match(text or '')
    if not m:
        return None
    name, args = m.group(1), m.group(2).strip()
    if name not in names:
        return None
    arguments = {}
    pos = 0
    while pos < len(args):
        am = _TEXT_ARG.match(args, pos)
        if not am:
            return None
        arguments[am.group(1)] = am.group(2) if am.group(2) is not None else am.group(3)
        pos = am.end()
    return ToolCall(name, arguments)


def _tool_call_from_api(entry):
    try:
        function = entry['function']
        name = function['name']
        raw = function.get('arguments') or ''
    except (KeyError, TypeError):
        raise AssistantError(NOT_UNDERSTOOD)
    if isinstance(raw, dict):
        arguments = raw
    else:
        try:
            arguments = json.loads(raw) if raw.strip() else {}
        except ValueError:
            raise AssistantError(NOT_UNDERSTOOD)
    if not isinstance(name, str) or not isinstance(arguments, dict):
        raise AssistantError(NOT_UNDERSTOOD)
    call_id = entry.get('id')
    return ToolCall(name, arguments, call_id) if call_id else ToolCall(name, arguments)


def complete(messages, tools, model=None):
    """
    one round with the model: messages is the system prompt plus the history,
    tools the openai-style definitions it may call. returns a ModelReply.
    """
    payload = {
        'model': model or cfg.ai_model,
        'temperature': 0,
        'stream': False,
        'max_tokens': MAX_TOKENS,
        'messages': messages,
        # llama.cpp field: without it gemma 4 thinks first and, on a hard
        # question, spends the whole budget on that; the answer comes back empty
        'chat_template_kwargs': {'enable_thinking': False},
    }
    if tools:
        payload['tools'] = tools
    data = post('chat/completions', json=payload)
    try:
        message = data['choices'][0]['message']
    except (KeyError, IndexError, TypeError):
        raise AssistantError(UNREADABLE)
    tool_calls = message.get('tool_calls') or []
    if tool_calls:
        # one command per request: only the first call counts
        return ModelReply(tool_call=_tool_call_from_api(tool_calls[0]))
    content = (message.get('content') or '').strip()
    names = {t['function']['name'] for t in tools or ()}
    call = parse_text_tool_call(content, names)
    if call:
        return ModelReply(tool_call=call)
    if not content:
        raise AssistantError("leere antwort vom KI-server")
    return ModelReply(text=content)


def transcribe(wav, filename='speech.wav'):
    """
    the text whisper hears in wav (bytes, 16 kHz mono 16 bit); empty speech
    is AssistantError("nichts verstanden").
    """
    data = post(
        'audio/transcriptions',
        data={'model': cfg.ai_whisper_model, 'prompt': WHISPER_PROMPT},
        files={'file': (filename, wav, 'audio/wav')},
        read_timeout=WHISPER_READ_TIMEOUT)
    try:
        text = data['text']
    except (KeyError, TypeError):
        raise AssistantError(UNREADABLE)
    text = ' '.join(str(text or '').split())
    if not text:
        raise AssistantError(NOTHING_HEARD)
    return text
