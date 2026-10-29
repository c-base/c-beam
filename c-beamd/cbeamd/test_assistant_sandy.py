"""
tests for cbeamd.assistant.sandy: sandy strands over a faked websocket, and
the dispatch in knowledge.py.
"""

import json
from unittest import mock

import pytest
from websocket import ABNF, WebSocketException, WebSocketTimeoutException

import cbeamdcfg as cfg
from cbeamd.assistant import knowledge, sandy
from cbeamd.assistant.chat import AssistantError


class FakeSocket:
    """plays back frames: ('text', dict) or ('binary', bytes) or ('close',) or an exception."""

    def __init__(self, frames):
        self.frames = list(frames)
        self.sent = []
        self.timeouts = []
        self.closed = False

    def send(self, data):
        self.sent.append(json.loads(data))

    def settimeout(self, value):
        self.timeouts.append(value)

    def recv_data(self):
        if not self.frames:
            raise WebSocketTimeoutException()
        frame = self.frames.pop(0)
        if isinstance(frame, Exception):
            raise frame
        if frame[0] == 'text':
            return ABNF.OPCODE_TEXT, json.dumps(frame[1]).encode()
        if frame[0] == 'raw':
            return ABNF.OPCODE_TEXT, frame[1]
        if frame[0] == 'binary':
            return ABNF.OPCODE_BINARY, frame[1]
        return ABNF.OPCODE_CLOSE, b''

    def close(self):
        self.closed = True


@pytest.fixture(autouse=True)
def configured(monkeypatch):
    monkeypatch.setattr(cfg, 'sandy_url', 'wss://sandy.test/ws/voice')
    monkeypatch.setattr(cfg, 'knowledge_source', 'sandy')


@pytest.fixture
def connect():
    with mock.patch('cbeamd.assistant.sandy.create_connection') as m:
        yield m


def test_ask_sets_the_voice_sends_the_question_and_reads_the_final_text(connect):
    ws = FakeSocket([
        ('text', {'type': 'sys_log', 'text': 'thinking'}),
        ('text', {'type': 'tool_log', 'text': 'rag'}),
        ('binary', b'\x00\x01' * 100),
        ('text', {'type': 'bot_text', 'text': 'Die c-base hat', 'done': False}),
        ('text', {'type': 'bot_text', 'text': 'Die c-base hat sieben Ringe.  Noch etwas?', 'done': True,
                  'sources': [{'src': 'lore/ringe.md'}, {'path': 'wiki/ringe'}, {'src': 'lore/ringe.md'}]}),
    ])
    connect.return_value = ws
    result = sandy.ask('wieviele ringe hat die c-base')
    connect.assert_called_once_with('wss://sandy.test/ws/voice', timeout=sandy.CONNECT_TIMEOUT)
    assert ws.sent == [
        {'type': 'control', 'action': 'set_voice', 'voice': 'de'},
        {'type': 'text_input', 'text': 'wieviele ringe hat die c-base'},
    ]
    assert result == (
        sandy.HEADER % 'wieviele ringe hat die c-base' + '\n\n'
        'Die c-base hat sieben Ringe. Noch etwas?\n\n'
        'Quellen: lore/ringe.md, wiki/ringe')
    assert ws.closed
    assert all(0 < t <= sandy.ANSWER_TIMEOUT for t in ws.timeouts)


def test_empty_or_closed_answers_are_nothing_found(connect):
    connect.return_value = FakeSocket([('text', {'type': 'bot_text', 'text': '  ', 'done': True})])
    assert sandy.ask('x') == sandy.NOTHING % 'x'
    connect.return_value = FakeSocket([('close',)])
    assert sandy.ask('x') == sandy.NOTHING % 'x'


def test_long_answers_are_cut(connect):
    connect.return_value = FakeSocket([('text', {'type': 'bot_text', 'text': 'a' * 2000, 'done': True})])
    result = sandy.ask('x')
    body = result.split('\n\n')[1]
    assert len(body) == sandy.MAX_CHARS and body.endswith('…')


def test_error_frame(connect):
    connect.return_value = FakeSocket([('text', {'type': 'error', 'message': 'model  down'})])
    with pytest.raises(AssistantError, match='sandy strands: model down'):
        sandy.ask('x')


def test_garbage_frames_are_skipped(connect):
    connect.return_value = FakeSocket([
        ('raw', b'not json'),
        ('text', ['a', 'list']),
        ('text', {'type': 'bot_text', 'text': 'ok', 'done': True}),
    ])
    assert 'ok' in sandy.ask('x')


def test_timeout_and_connection_failures(connect):
    connect.return_value = FakeSocket([])   # recv times out
    with pytest.raises(AssistantError, match='antwortet nicht'):
        sandy.ask('x')
    connect.return_value = FakeSocket([WebSocketException('reset')])
    with pytest.raises(AssistantError, match='verbindung abgebrochen'):
        sandy.ask('x')
    connect.side_effect = OSError('refused')
    with pytest.raises(AssistantError, match='nicht erreichbar'):
        sandy.ask('x')


def test_deadline_is_enforced(connect, monkeypatch):
    clock = iter([0.0, 100.0, 200.0])
    monkeypatch.setattr(sandy.time, 'monotonic', lambda: next(clock))
    connect.return_value = FakeSocket([('text', {'type': 'bot_text', 'text': 'late', 'done': True})])
    with pytest.raises(AssistantError, match='antwortet nicht'):
        sandy.ask('x')


def test_unconfigured(connect, monkeypatch):
    monkeypatch.setattr(cfg, 'sandy_url', '')
    assert not sandy.configured()
    with pytest.raises(AssistantError, match='nicht konfiguriert'):
        sandy.ask('x')
    connect.assert_not_called()


# dispatch -----------------------------------------------------------------------

def test_knowledge_uses_sandy_when_configured_so(connect, monkeypatch):
    monkeypatch.setattr(cfg, 'rag_key', '')
    assert knowledge.configured()
    connect.return_value = FakeSocket([('text', {'type': 'bot_text', 'text': 'sieben', 'done': True})])
    assert 'sieben' in knowledge.search('ringe')
    monkeypatch.setattr(cfg, 'sandy_url', '')
    assert not knowledge.configured()


def test_knowledge_uses_qdrant_otherwise(connect, monkeypatch):
    monkeypatch.setattr(cfg, 'knowledge_source', 'qdrant')
    monkeypatch.setattr(cfg, 'rag_url', 'http://qdrant.test')
    monkeypatch.setattr(cfg, 'rag_key', '')
    assert not knowledge.configured()
    monkeypatch.setattr(cfg, 'rag_key', 'secret')
    assert knowledge.configured()
    connect.assert_not_called()
