"""
tests for cbeamd.assistant.engine (the rounds of one request) and the views
in cbeamd.views.assistant, with the model mocked.
"""

import json
from unittest import mock

import pytest
from django.contrib.auth import get_user_model
from django.test import Client

import cbeamdcfg as cfg
from cbeamd.assistant import conversation as conv, engine, tools
from cbeamd.assistant.chat import AssistantError, ModelReply, ToolCall
from cbeamd.models import Status


@pytest.fixture(autouse=True)
def configured(monkeypatch):
    monkeypatch.setattr(cfg, 'ai_url', 'http://ai.test/v1/')
    monkeypatch.setattr(cfg, 'rag_key', '')
    monkeypatch.setattr(tools, '_sounds_cache', (0.0, []))
    with mock.patch('cbeamd.assistant.tools.rpc_sounds', return_value=['siri.mp3']):
        yield


@pytest.fixture
def client(db, settings):
    # the default hasher takes seconds per user on purpose; these tests only need a session
    settings.PASSWORD_HASHERS = ['django.contrib.auth.hashers.MD5PasswordHasher']
    client = Client()
    client.force_login(get_user_model().objects.create_user('smile', password='pw'))
    return client


@pytest.fixture
def complete():
    with mock.patch('cbeamd.assistant.engine.chat.complete') as m:
        yield m


def ask(client, text, voice=False):
    response = client.post('/assistant/ask', json.dumps({'text': text, 'voice': voice}), content_type='application/json')
    return response, response.json() if response['Content-Type'].startswith('application/json') else None


def confirm(client, call_id, accept):
    response = client.post('/assistant/confirm', json.dumps({'id': call_id, 'accept': accept}), content_type='application/json')
    return response, response.json()


def history(client):
    return client.session[conv.SESSION_KEY]['messages']


def call(name, arguments=None, call_id='c1'):
    return ModelReply(tool_call=ToolCall(name, arguments or {}, call_id))


# the page ---------------------------------------------------------------------------

def test_page_needs_login(db):
    response = Client().get('/assistant')
    assert response.status_code == 302
    assert response['Location'].startswith('/login/')


def test_page_renders_the_terminal(client):
    response = client.get('/assistant')
    assert response.status_code == 200
    content = response.content.decode()
    assert 'smile@c-beam&gt;' in content
    assert 'data-ask-url="/assistant/ask"' in content
    assert 'data-configured="1"' in content
    assert 'assistant.js' in content
    assert 'href="/assistant">c-beam fragen</a>' in content


def test_page_says_when_the_server_is_not_configured(client, monkeypatch):
    monkeypatch.setattr(cfg, 'ai_url', '')
    content = client.get('/assistant').content.decode()
    assert 'data-configured="0"' in content
    assert 'KI-server nicht konfiguriert' in content


# the endpoints ----------------------------------------------------------------------

def test_endpoints_refuse_anonymous_with_json(db):
    response = Client().post('/assistant/ask', '{"text": "hi"}', content_type='application/json')
    assert response.status_code == 403
    assert response.json()['lines'] == [{'kind': 'error', 'text': 'fehler: nicht eingeloggt'}]


def test_endpoints_want_post(client):
    assert client.get('/assistant/ask').status_code == 405
    assert client.get('/assistant/confirm').status_code == 405


def test_bad_bodies_are_400(client):
    assert client.post('/assistant/ask', 'not json', content_type='application/json').status_code == 400
    assert client.post('/assistant/ask', '[1]', content_type='application/json').status_code == 400
    assert client.post('/assistant/ask', '{"text": 5}', content_type='application/json').status_code == 400
    assert client.post('/assistant/confirm', '{"accept": true}', content_type='application/json').status_code == 400


def test_empty_text_is_not_understood(client, complete):
    response, data = ask(client, '   ')
    assert response.status_code == 200
    assert data['lines'] == [{'kind': 'error', 'text': 'fehler: nichts verstanden'}]
    complete.assert_not_called()


def test_unconfigured_server(client, complete, monkeypatch):
    monkeypatch.setattr(cfg, 'ai_url', '')
    assert ask(client, 'hallo')[1]['lines'][0]['text'] == 'fehler: KI-server nicht konfiguriert'
    complete.assert_not_called()


# rounds -------------------------------------------------------------------------------

def test_plain_answer(client, complete):
    complete.return_value = ModelReply(text='Hallo smile, was kann ich tun?')
    response, data = ask(client, 'hallo')
    assert data == {
        'lines': [{'kind': 'answer', 'text': 'hallo smile, was kann ich tun?'}],
        'speak': 'Hallo smile, was kann ich tun?',
        'confirm': None,
    }
    assert history(client) == [
        {'role': 'user', 'content': 'hallo'},
        {'role': 'assistant', 'content': 'Hallo smile, was kann ich tun?'},
    ]
    messages, definitions = complete.call_args.args
    assert messages[0]['role'] == 'system'
    assert 'Der sprechende Nutzer heißt smile.' in messages[0]['content']
    assert 'getippte Sätze' in messages[0]['content']
    assert messages[1:] == [{'role': 'user', 'content': 'hallo'}]
    assert {d['function']['name'] for d in definitions} == {
        'who_is_on_board', 'bar_status', 'events_today', 'missions', 'artefacts',
        'login', 'logout', 'announce', 'play_sound'}


def test_voice_flag_picks_the_spoken_prompt(client, complete):
    complete.return_value = ModelReply(text='ok')
    ask(client, 'hallo', voice=True)
    assert 'erkannt per Spracherkennung' in complete.call_args.args[0][0]['content']


def test_knowledge_paragraph_follows_the_tool(client, complete, monkeypatch):
    complete.return_value = ModelReply(text='ok')
    ask(client, 'hallo')
    assert 'station_knowledge' not in complete.call_args.args[0][0]['content']
    monkeypatch.setattr(cfg, 'rag_key', 'secret')
    ask(client, 'hallo')
    assert 'station_knowledge' in complete.call_args.args[0][0]['content']


def test_query_tool_feeds_the_model(client, complete):
    Status.objects.create(bar_open=True)
    complete.side_effect = [call('bar_status'), ModelReply(text='Die Bar ist geöffnet.')]
    response, data = ask(client, 'ist die bar offen?')
    assert data['lines'] == [{'kind': 'answer', 'text': 'die bar ist geöffnet.'}]
    assert history(client) == [
        {'role': 'user', 'content': 'ist die bar offen?'},
        ToolCall('bar_status', {}, 'c1').message(),
        {'role': 'tool', 'tool_call_id': 'c1', 'content': 'geöffnet'},
        {'role': 'assistant', 'content': 'Die Bar ist geöffnet.'},
    ]
    # the second round saw the tool result
    second = complete.call_args_list[1].args[0]
    assert second[-1] == {'role': 'tool', 'tool_call_id': 'c1', 'content': 'geöffnet'}


def test_third_round_shows_the_tool_result(client, complete):
    Status.objects.create(bar_open=False)
    complete.side_effect = [call('bar_status', call_id='c1'), call('who_is_on_board', call_id='c2'), call('bar_status', call_id='c3')]
    response, data = ask(client, 'und jetzt?')
    assert data['lines'] == [{'kind': 'answer', 'text': 'geschlossen'}]
    assert data['speak'] == 'geschlossen'
    assert complete.call_count == 3
    assert [m['role'] for m in history(client)] == ['user', 'assistant', 'tool', 'assistant', 'tool', 'assistant', 'tool']


def test_self_tool_runs_at_once(client, complete):
    complete.return_value = call('login')
    with mock.patch('cbeamd.assistant.tools.force_login') as login:
        response, data = ask(client, 'log mich ein')
    login.assert_called_once()
    assert login.call_args.args[1] == 'smile'
    assert data['lines'] == [{'kind': 'done', 'text': 'ausgefu:hrt: einloggen als smile'}]
    assert data['speak'] == 'Erledigt.'
    assert complete.call_count == 1
    assert history(client)[-1] == {'role': 'tool', 'tool_call_id': 'c1', 'content': 'ausgeführt'}


def test_confirm_tool_waits_for_the_user(client, complete):
    complete.return_value = call('announce', {'text': 'Essen ist fertig'})
    with mock.patch('cbeamd.assistant.tools.rpc_announce') as rpc:
        response, data = ask(client, 'sag allen dass essen fertig ist')
        rpc.assert_not_called()
        assert data == {
            'lines': [{'kind': 'confirm', 'text': 'durchsage: „Essen ist fertig“ [j/n]'}],
            'speak': 'durchsage: „Essen ist fertig“. Ausführen?',
            'confirm': {'id': 'c1', 'description': 'durchsage: „Essen ist fertig“'},
        }
        assert client.session[conv.SESSION_KEY]['pending']['id'] == 'c1'

        response, data = confirm(client, 'c1', True)
        rpc.assert_called_once()
        assert rpc.call_args.args[1] == 'Essen ist fertig'
    assert data['lines'] == [{'kind': 'done', 'text': 'ausgefu:hrt: durchsage: „Essen ist fertig“'}]
    assert data['speak'] == 'Erledigt.'
    assert client.session[conv.SESSION_KEY]['pending'] is None
    assert history(client)[-1] == {'role': 'tool', 'tool_call_id': 'c1', 'content': 'ausgeführt'}


def test_rejected_proposal(client, complete):
    complete.return_value = call('play_sound', {'sound': 'siri.mp3'})
    with mock.patch('cbeamd.assistant.tools.rpc_play') as rpc:
        ask(client, 'spiel siri')
        response, data = confirm(client, 'c1', False)
        rpc.assert_not_called()
    assert data['lines'] == [{'kind': 'info', 'text': 'verworfen: sound: siri.mp3'}]
    assert data['speak'] is None
    assert history(client)[-1] == {'role': 'tool', 'tool_call_id': 'c1', 'content': conv.REJECTED}


def test_confirm_without_or_with_wrong_proposal(client, complete):
    assert confirm(client, 'c9', True)[1]['lines'][0]['text'] == 'fehler: kein offener vorschlag'
    complete.return_value = call('announce', {'text': 'x'})
    ask(client, 'durchsage x')
    assert confirm(client, 'c9', True)[1]['lines'][0]['text'] == 'fehler: kein offener vorschlag'
    assert client.session[conv.SESSION_KEY]['pending']['id'] == 'c1'


def test_a_new_request_drops_the_proposal(client, complete):
    complete.return_value = call('announce', {'text': 'x'})
    ask(client, 'durchsage x')
    complete.return_value = ModelReply(text='Niemand.')
    ask(client, 'wer ist da?')
    assert client.session[conv.SESSION_KEY]['pending'] is None
    assert history(client)[2] == {'role': 'tool', 'tool_call_id': 'c1', 'content': conv.REJECTED}


def test_failed_confirmation_is_recorded_as_rejected(client, complete):
    complete.return_value = call('announce', {'text': 'x'})
    ask(client, 'durchsage x')
    with mock.patch('cbeamd.assistant.tools.rpc_announce', side_effect=RuntimeError('shout down')):
        response, data = confirm(client, 'c1', True)
    assert data['lines'] == [{'kind': 'error', 'text': 'fehler: durchsage: „x“ fehlgeschlagen'}]
    assert history(client)[-1]['content'] == conv.REJECTED


def test_confirm_counts_as_activity(client, complete):
    complete.return_value = call('announce', {'text': 'x'})
    ask(client, 'durchsage x')
    before = client.session[conv.SESSION_KEY]['last']
    with mock.patch('cbeamd.assistant.engine.Conversation.touch') as touch:
        confirm(client, 'c1', False)
    touch.assert_called_once()


# failures ----------------------------------------------------------------------------

def test_model_error_rolls_back(client, complete):
    complete.return_value = ModelReply(text='Hallo.')
    ask(client, 'hallo')
    complete.side_effect = AssistantError('KI-server ausgelastet')
    response, data = ask(client, 'und jetzt?')
    assert data['lines'] == [{'kind': 'error', 'text': 'fehler: KI-server ausgelastet'}]
    assert history(client) == [{'role': 'user', 'content': 'hallo'}, {'role': 'assistant', 'content': 'Hallo.'}]


def test_unknown_tool_rolls_back(client, complete):
    complete.return_value = call('say', {'text': 'hi'})
    response, data = ask(client, 'sag hi')
    assert data['lines'] == [{'kind': 'error', 'text': 'fehler: nicht verstanden'}]
    assert history(client) == []


def test_tool_failure_rolls_back(client, complete):
    complete.return_value = call('who_is_on_board')
    with mock.patch('cbeamd.assistant.tools.userlist', side_effect=RuntimeError('db')):
        response, data = ask(client, 'wer ist da?')
    assert data['lines'] == [{'kind': 'error', 'text': 'fehler: wer ist an bord fehlgeschlagen'}]
    assert history(client) == []


def test_unexpected_exception_is_an_internal_error(client, complete):
    complete.side_effect = RuntimeError('boom')
    response, data = ask(client, 'hallo')
    assert response.status_code == 200
    assert data['lines'] == [{'kind': 'error', 'text': 'fehler: interner fehler'}]
    assert history(client) == []


def test_refusal_is_shown_but_not_kept(client, complete):
    complete.return_value = ModelReply(text='Das kann ich nicht.')
    response, data = ask(client, 'mach die bar auf')
    assert data['lines'] == [{'kind': 'answer', 'text': 'das kann ich nicht.'}]
    assert history(client) == [{'role': 'user', 'content': 'mach die bar auf'}]


def test_follow_up_sees_the_history(client, complete):
    complete.return_value = ModelReply(text='Der Fernsehturm ist 368 Meter hoch.')
    ask(client, 'wie hoch ist der fernsehturm?')
    complete.return_value = ModelReply(text='Das sind 1207 Fuß.')
    ask(client, 'und in fuß?')
    messages = complete.call_args.args[0]
    assert [m['role'] for m in messages] == ['system', 'user', 'assistant', 'user']
    assert messages[-1] == {'role': 'user', 'content': 'und in fuß?'}


# transcription ---------------------------------------------------------------------

from django.core.files.uploadedfile import SimpleUploadedFile  # noqa: E402


def upload(client, data=b'RIFF....', name='speech.wav'):
    return client.post('/assistant/transcribe', {'file': SimpleUploadedFile(name, data, content_type='audio/wav')})


def test_transcribe_hands_the_wav_to_whisper(client):
    with mock.patch('cbeamd.views.assistant.chat.transcribe', return_value='ist die bar offen?') as transcribe:
        response = upload(client, b'RIFF....')
    assert response.status_code == 200
    assert response.json() == {'text': 'ist die bar offen?', 'error': None}
    transcribe.assert_called_once_with(b'RIFF....', 'speech.wav')


def test_transcribe_reports_whisper_errors_as_text(client):
    with mock.patch('cbeamd.views.assistant.chat.transcribe', side_effect=AssistantError('nichts verstanden')):
        response = upload(client)
    assert response.status_code == 200
    assert response.json() == {'text': None, 'error': 'nichts verstanden'}


def test_transcribe_refuses_anonymous_missing_and_huge_uploads(db, client):
    assert Client().post('/assistant/transcribe', {}).status_code == 403
    assert client.post('/assistant/transcribe', {}).status_code == 400
    assert client.get('/assistant/transcribe').status_code == 405
    with mock.patch('cbeamd.views.assistant.chat.transcribe') as transcribe:
        response = upload(client, b'x' * (2 * 1024 * 1024 + 1))
    assert response.status_code == 400
    assert response.json()['error'] == 'aufnahme zu groß'
    transcribe.assert_not_called()


def test_page_offers_the_microphone_hooks(client):
    content = client.get('/assistant').content.decode()
    assert 'data-transcribe-url="/assistant/transcribe"' in content
    assert 'assistant-worklet.js' in content
    assert 'id="assistant-mic"' in content
