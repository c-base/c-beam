"""
tests for cbeamd.assistant.chat: the http side of the web assistant, against a
mocked requests.post.
"""

import json
from unittest import mock

import pytest
import requests

import cbeamdcfg as cfg
from cbeamd.assistant import chat
from cbeamd.assistant.chat import AssistantError, ModelReply, ToolCall, parse_text_tool_call

TOOLS = [
    {'type': 'function', 'function': {'name': 'station_knowledge', 'parameters': {}}},
    {'type': 'function', 'function': {'name': 'who_is_on_board', 'parameters': {}}},
]
MESSAGES = [{'role': 'system', 'content': 'du bist c-beam'}, {'role': 'user', 'content': 'wer ist da?'}]


class FakeResponse:
    def __init__(self, status=200, body=None, headers=None):
        self.status_code = status
        self.ok = status < 400
        self.headers = headers or {}
        self._body = body
        self.text = json.dumps(body) if body is not None else ''

    def json(self):
        if self._body is None:
            raise ValueError("no json")
        return self._body


def reply(message):
    return FakeResponse(body={'choices': [{'message': message}]})


@pytest.fixture(autouse=True)
def ai_configured(monkeypatch):
    monkeypatch.setattr(cfg, 'ai_url', 'http://ai.test/v1/')
    monkeypatch.setattr(cfg, 'ai_model', 'test-model')
    monkeypatch.setattr(cfg, 'ai_connect_timeout', 5)
    monkeypatch.setattr(cfg, 'ai_read_timeout', 60)


@pytest.fixture
def post():
    with mock.patch('cbeamd.assistant.chat.requests.request') as p:
        yield p


@pytest.fixture
def sleep():
    with mock.patch('cbeamd.assistant.chat.time.sleep') as s:
        yield s


# request shape ---------------------------------------------------------------

def test_complete_sends_the_app_payload(post):
    post.return_value = reply({'content': 'niemand'})
    chat.complete(MESSAGES, TOOLS)
    args, kwargs = post.call_args
    assert args == ('POST', 'http://ai.test/v1/chat/completions')
    assert kwargs['timeout'] == (5, 60)
    payload = kwargs['json']
    assert payload['model'] == 'test-model'
    assert payload['temperature'] == 0
    assert payload['stream'] is False
    assert payload['max_tokens'] == chat.MAX_TOKENS
    assert payload['messages'] == MESSAGES
    assert payload['tools'] == TOOLS
    assert payload['chat_template_kwargs'] == {'enable_thinking': False}


def test_complete_without_tools_sends_no_tools_field(post):
    post.return_value = reply({'content': 'vier'})
    chat.complete(MESSAGES, [])
    assert 'tools' not in post.call_args.kwargs['json']


def test_complete_uses_the_given_model(post):
    post.return_value = reply({'content': 'ok'})
    chat.complete(MESSAGES, [], model='other')
    assert post.call_args.kwargs['json']['model'] == 'other'


def test_unconfigured_server_is_an_error(post, monkeypatch):
    monkeypatch.setattr(cfg, 'ai_url', '')
    assert not chat.configured()
    with pytest.raises(AssistantError, match='nicht konfiguriert'):
        chat.complete(MESSAGES, [])
    post.assert_not_called()


# response shapes -------------------------------------------------------------

def test_text_answer(post):
    post.return_value = reply({'content': '  Niemand ist an Bord.  '})
    result = chat.complete(MESSAGES, TOOLS)
    assert result == ModelReply(text='Niemand ist an Bord.')


def test_first_tool_call_only(post):
    post.return_value = reply({
        'content': None,
        'tool_calls': [
            {'id': 'call_1', 'type': 'function',
             'function': {'name': 'station_knowledge', 'arguments': '{"query": "wlan"}'}},
            {'id': 'call_2', 'type': 'function',
             'function': {'name': 'who_is_on_board', 'arguments': '{}'}},
        ],
    })
    result = chat.complete(MESSAGES, TOOLS)
    assert result.text is None
    assert result.tool_call == ToolCall('station_knowledge', {'query': 'wlan'}, 'call_1')


def test_tool_call_with_empty_arguments(post):
    post.return_value = reply({'tool_calls': [{'id': 'c', 'function': {'name': 'who_is_on_board', 'arguments': ''}}]})
    assert chat.complete(MESSAGES, TOOLS).tool_call == ToolCall('who_is_on_board', {}, 'c')


def test_tool_call_with_dict_arguments(post):
    post.return_value = reply({'tool_calls': [{'function': {'name': 'station_knowledge', 'arguments': {'query': 'bar'}}}]})
    call = chat.complete(MESSAGES, TOOLS).tool_call
    assert call.name == 'station_knowledge'
    assert call.arguments == {'query': 'bar'}
    assert call.id.startswith('call_')


def test_broken_tool_arguments_are_not_understood(post):
    post.return_value = reply({'tool_calls': [{'id': 'c', 'function': {'name': 'station_knowledge', 'arguments': '{"query": '}}]})
    with pytest.raises(AssistantError, match='nicht verstanden'):
        chat.complete(MESSAGES, TOOLS)


def test_non_object_tool_arguments_are_not_understood(post):
    post.return_value = reply({'tool_calls': [{'id': 'c', 'function': {'name': 'station_knowledge', 'arguments': '[1, 2]'}}]})
    with pytest.raises(AssistantError, match='nicht verstanden'):
        chat.complete(MESSAGES, TOOLS)


def test_text_shaped_tool_call_becomes_a_call(post):
    post.return_value = reply({'content': 'station_knowledge(query="wlan passwort")'})
    result = chat.complete(MESSAGES, TOOLS)
    assert result.text is None
    assert result.tool_call.name == 'station_knowledge'
    assert result.tool_call.arguments == {'query': 'wlan passwort'}


def test_text_that_looks_like_an_unknown_call_stays_text(post):
    post.return_value = reply({'content': 'sin(x)'})
    assert chat.complete(MESSAGES, TOOLS) == ModelReply(text='sin(x)')


def test_empty_answer_is_an_error(post):
    post.return_value = reply({'content': ''})
    with pytest.raises(AssistantError, match='leere antwort'):
        chat.complete(MESSAGES, TOOLS)


def test_unreadable_body_is_an_error(post):
    post.return_value = FakeResponse(body={'choices': []})
    with pytest.raises(AssistantError, match='unlesbare antwort'):
        chat.complete(MESSAGES, TOOLS)
    post.return_value = FakeResponse(body=None)
    with pytest.raises(AssistantError, match='unlesbare antwort'):
        chat.complete(MESSAGES, TOOLS)


# transport errors ------------------------------------------------------------

def test_short_retry_after_is_waited_out_once(post, sleep):
    post.side_effect = [FakeResponse(429, headers={'Retry-After': '2'}), reply({'content': 'ok'})]
    assert chat.complete(MESSAGES, TOOLS) == ModelReply(text='ok')
    sleep.assert_called_once_with(2)
    assert post.call_count == 2


def test_second_429_is_reported(post, sleep):
    post.side_effect = [FakeResponse(429, headers={'Retry-After': '1'}), FakeResponse(429, headers={'Retry-After': '1'})]
    with pytest.raises(AssistantError, match='ausgelastet, in 1 s nochmal'):
        chat.complete(MESSAGES, TOOLS)
    assert post.call_count == 2


def test_long_retry_after_is_reported_without_waiting(post, sleep):
    post.return_value = FakeResponse(429, headers={'Retry-After': '10'})
    with pytest.raises(AssistantError, match='ausgelastet, in 10 s nochmal'):
        chat.complete(MESSAGES, TOOLS)
    sleep.assert_not_called()
    assert post.call_count == 1


def test_429_without_retry_after_is_reported(post, sleep):
    post.return_value = FakeResponse(429)
    with pytest.raises(AssistantError, match='^KI-server ausgelastet$'):
        chat.complete(MESSAGES, TOOLS)
    sleep.assert_not_called()


def test_429_with_a_date_retry_after_is_reported(post, sleep):
    post.return_value = FakeResponse(429, headers={'Retry-After': 'Wed, 21 Oct 2026 07:28:00 GMT'})
    with pytest.raises(AssistantError, match='^KI-server ausgelastet$'):
        chat.complete(MESSAGES, TOOLS)
    sleep.assert_not_called()


def test_http_error_is_reported(post):
    post.return_value = FakeResponse(500, body={'error': 'boom'})
    with pytest.raises(AssistantError, match='HTTP 500'):
        chat.complete(MESSAGES, TOOLS)


def test_timeout_is_reported(post):
    post.side_effect = requests.Timeout()
    with pytest.raises(AssistantError, match='antwortet nicht'):
        chat.complete(MESSAGES, TOOLS)


def test_connection_error_is_reported(post):
    post.side_effect = requests.ConnectionError()
    with pytest.raises(AssistantError, match='nicht erreichbar'):
        chat.complete(MESSAGES, TOOLS)


def test_post_read_timeout_override(post):
    post.return_value = FakeResponse(body={'text': 'hallo'})
    assert chat.post('audio/transcriptions', files={'file': b''}, read_timeout=30) == {'text': 'hallo'}
    assert post.call_args.kwargs['timeout'] == (5, 30)


# text-shaped tool calls ------------------------------------------------------

NAMES = {'station_knowledge', 'say', 'who_is_on_board'}


def test_parse_double_quoted_argument():
    call = parse_text_tool_call('station_knowledge(query="wlan")', NAMES)
    assert (call.name, call.arguments) == ('station_knowledge', {'query': 'wlan'})


def test_parse_single_quoted_and_multiple_arguments():
    call = parse_text_tool_call(" say(text='hallo, welt', voice=\"r2d2\") \n", NAMES)
    assert (call.name, call.arguments) == ('say', {'text': 'hallo, welt', 'voice': 'r2d2'})


def test_parse_call_without_arguments():
    call = parse_text_tool_call('who_is_on_board()', NAMES)
    assert (call.name, call.arguments) == ('who_is_on_board', {})


def test_parse_rejects_unknown_name_and_plain_text():
    assert parse_text_tool_call('login()', NAMES) is None
    assert parse_text_tool_call('die bar ist offen (seit 19 uhr)', NAMES) is None
    assert parse_text_tool_call('', NAMES) is None
    assert parse_text_tool_call(None, NAMES) is None


def test_parse_rejects_unquoted_or_positional_arguments():
    assert parse_text_tool_call('station_knowledge(wlan)', NAMES) is None
    assert parse_text_tool_call('station_knowledge(query=wlan)', NAMES) is None
    assert parse_text_tool_call('station_knowledge("wlan")', NAMES) is None


def test_tool_call_message_records_the_call_in_chat_format():
    call = ToolCall('station_knowledge', {'query': 'wlan'}, 'call_1')
    assert call.message() == {
        'role': 'assistant',
        'content': None,
        'tool_calls': [{'id': 'call_1', 'type': 'function',
                        'function': {'name': 'station_knowledge', 'arguments': '{"query": "wlan"}'}}],
    }


# whisper ----------------------------------------------------------------------

def test_transcribe_sends_the_wav_with_the_spelling_prompt(post, monkeypatch):
    monkeypatch.setattr(cfg, 'ai_whisper_model', 'whisper-test')
    post.return_value = FakeResponse(body={'text': '  Ist die  Bar offen? '})
    assert chat.transcribe(b'RIFF....', 'speech.wav') == 'Ist die Bar offen?'
    args, kwargs = post.call_args
    assert args == ('POST', 'http://ai.test/v1/audio/transcriptions')
    assert kwargs['data'] == {'model': 'whisper-test', 'prompt': chat.WHISPER_PROMPT}
    assert kwargs['files'] == {'file': ('speech.wav', b'RIFF....', 'audio/wav')}
    assert kwargs['json'] is None
    assert kwargs['timeout'] == (5, chat.WHISPER_READ_TIMEOUT)


def test_transcribe_empty_result_is_nothing_heard(post):
    post.return_value = FakeResponse(body={'text': '   '})
    with pytest.raises(AssistantError, match='nichts verstanden'):
        chat.transcribe(b'wav')
    post.return_value = FakeResponse(body={'text': None})
    with pytest.raises(AssistantError, match='nichts verstanden'):
        chat.transcribe(b'wav')


def test_transcribe_unreadable_and_busy(post, sleep):
    post.return_value = FakeResponse(body={'result': 'x'})
    with pytest.raises(AssistantError, match='unlesbare antwort'):
        chat.transcribe(b'wav')
    post.return_value = FakeResponse(429)
    with pytest.raises(AssistantError, match='ausgelastet'):
        chat.transcribe(b'wav')


# the model list -------------------------------------------------------------

@pytest.fixture
def fresh_models():
    chat.reset_models()
    yield
    chat.reset_models()


def test_models_lists_chat_models_without_embeddings(post, fresh_models):
    post.return_value = FakeResponse(body={'data': [
        {'id': 'Gemma-4-E4B-it-MTP-GGUF', 'labels': ['custom', 'tool-calling', 'vision']},
        {'id': 'Qwen3-Coder-Next-GGUF', 'labels': ['coding', 'tool-calling']},
        {'id': 'nomic-embed-text-v1-GGUF', 'labels': ['embeddings']},
        {'id': 'some-embed-model', 'labels': []},
        {'labels': ['broken']},
        'garbage',
    ]})
    assert chat.models() == [
        {'id': 'Gemma-4-E4B-it-MTP-GGUF', 'labels': ['custom', 'tool-calling', 'vision']},
        {'id': 'Qwen3-Coder-Next-GGUF', 'labels': ['coding', 'tool-calling']},
    ]
    args, kwargs = post.call_args
    assert args == ('GET', 'http://ai.test/v1/models')
    assert kwargs['timeout'] == (5, 10)


def test_models_are_cached(post, fresh_models):
    post.return_value = FakeResponse(body={'data': [{'id': 'm', 'labels': []}]})
    chat.models()
    chat.models()
    assert post.call_count == 1


def test_models_are_empty_when_the_server_cannot_be_asked(post, fresh_models):
    post.side_effect = requests.ConnectionError()
    assert chat.models() == []
    post.return_value = FakeResponse(body={'nope': 1})
    chat.reset_models()
    assert chat.models() == []
