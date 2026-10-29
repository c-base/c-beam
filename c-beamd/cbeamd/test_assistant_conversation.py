"""
tests for cbeamd.assistant.prompt and cbeamd.assistant.conversation.
"""

import json
from datetime import datetime
from zoneinfo import ZoneInfo

from django.contrib.sessions.backends.db import SessionStore
import pytest

from cbeamd.assistant import conversation as conv, prompt
from cbeamd.assistant.chat import ToolCall
from cbeamd.assistant.conversation import Conversation, trim


# prompt -----------------------------------------------------------------------------

BERLIN = ZoneInfo('Europe/Berlin')


def test_format_now_is_german_and_local():
    when = datetime(2026, 10, 29, 13, 5, tzinfo=ZoneInfo('UTC'))  # 14:05 in berlin, a thursday
    assert prompt.format_now(when) == 'Donnerstag, 29. Oktober 2026, 14:05'
    assert prompt.format_now(datetime(2026, 3, 1, 0, 0, tzinfo=BERLIN)) == 'Sonntag, 1. März 2026, 00:00'


def test_prompt_names_user_and_time():
    text = prompt.build('smile', now=datetime(2026, 10, 29, 14, 5, tzinfo=BERLIN))
    assert text.startswith('Du bist c-beam, der Bordcomputer der Raumstation c-base in Berlin.')
    assert 'Der sprechende Nutzer heißt smile. Jetzt ist Donnerstag, 29. Oktober 2026, 14:05.' in text
    assert '{' not in text and '}' not in text


def test_prompt_without_knowledge_source_has_no_knowledge_paragraph():
    text = prompt.build('smile')
    assert 'station_knowledge' not in text
    assert 'Datenrettungssonde' not in text
    assert 'beantwortest du mit Hilfe der Werkzeuge. Alle anderen Fragen' in text


def test_prompt_with_knowledge_source_forces_lookups():
    text = prompt.build('smile', knowledge=True)
    assert 'indem du zuerst das Werkzeug station_knowledge aufrufst' in text
    assert 'die datenrettungssonde siri enthält diese information leider auch nicht' in text


def test_voice_and_typed_variants():
    voice = prompt.build('smile', knowledge=True, voice=True)
    typed = prompt.build('smile', knowledge=True, voice=False)
    assert 'erkannt per Spracherkennung' in voice
    assert 'Die Spracherkennung schreibt c-base oft als „Seabase“' in voice
    assert 'Spracherkennung' not in typed
    assert 'getippte Sätze' in typed
    assert 'in Suchanfragen schreibst du c-base' in typed


def test_system_message():
    message = prompt.system_message('smile')
    assert message['role'] == 'system'
    assert message['content'].startswith('Du bist c-beam')
    assert 'Der sprechende Nutzer heißt smile.' in message['content']


# refusals and trimming -------------------------------------------------------------

@pytest.mark.parametrize('text', [
    'Das kann ich nicht.',
    'das kann ich leider nicht',
    'Das ist nicht möglich.',
    'Dafür habe ich kein Werkzeug.',
    'Dafür gibt es kein passendes Werkzeug.',
    'Ich weiß dazu nichts.',
    'die station weiss darüber nichts',
    'Dazu ist nichts bekannt.',
    'dazu weiß die station nichts. die datenrettungssonde siri enthält diese information leider auch nicht.',
])
def test_refusals_are_recognized(text):
    assert conv.is_refusal(text)


@pytest.mark.parametrize('text', ['Die Bar ist geöffnet.', 'An Bord sind alice und bob.', '', None])
def test_answers_are_not_refusals(text):
    assert not conv.is_refusal(text)


def user(i):
    return {'role': 'user', 'content': 'frage %d' % i}


def answer(i):
    return {'role': 'assistant', 'content': 'antwort %d' % i}


def test_trim_keeps_the_limit_and_a_user_message_first():
    messages = []
    for i in range(20):
        messages += [user(i), answer(i)]
    trim(messages)
    assert len(messages) == conv.MAX_MESSAGES
    assert messages[0] == user(8)
    assert messages[-1] == answer(19)


def test_trim_never_cuts_between_a_call_and_its_result():
    call = ToolCall('bar_status', {}, 'c1')
    messages = [user(0), call.message(), {'role': 'tool', 'tool_call_id': 'c1', 'content': 'geöffnet'}, answer(0)]
    for i in range(1, 12):
        messages += [user(i), answer(i)]
    assert len(messages) == 26
    trim(messages)
    # 24 would start at the tool result; the cut moves on to the next user message
    assert messages[0] == user(1)
    assert len(messages) == 22
    assert all(m['role'] != 'tool' for m in messages)


def test_trim_leaves_a_short_history_alone():
    messages = [user(0), answer(0)]
    assert trim(messages) == [user(0), answer(0)]


# conversation ------------------------------------------------------------------------

class Clock:
    def __init__(self, t=1000.0):
        self.t = t

    def __call__(self):
        return self.t


@pytest.fixture
def session():
    return {}


def test_a_request_is_recorded_and_saved(session):
    clock = Clock()
    c = Conversation(session, clock)
    c.begin()
    c.add_user('ist die bar offen?')
    call = ToolCall('bar_status', {}, 'c1')
    c.add_call(call)
    c.add_result('c1', 'geöffnet')
    assert c.add_answer('Die Bar ist geöffnet.')
    c.save()
    stored = session[conv.SESSION_KEY]
    assert stored['messages'] == [
        {'role': 'user', 'content': 'ist die bar offen?'},
        call.message(),
        {'role': 'tool', 'tool_call_id': 'c1', 'content': 'geöffnet'},
        {'role': 'assistant', 'content': 'Die Bar ist geöffnet.'},
    ]
    assert stored['pending'] is None
    assert stored['last'] == 1000.0
    json.dumps(stored)  # the session backend needs plain json


def test_history_survives_a_reload_within_three_minutes(session):
    clock = Clock()
    c = Conversation(session, clock)
    c.begin()
    c.add_user('hallo')
    c.add_answer('hallo smile')
    c.save()
    clock.t += conv.IDLE_SECONDS - 1
    assert Conversation(session, clock).messages == [{'role': 'user', 'content': 'hallo'}, {'role': 'assistant', 'content': 'hallo smile'}]
    clock.t += 2
    assert Conversation(session, clock).messages == []


def test_begin_stamps_the_time_of_the_last_request(session):
    clock = Clock()
    c = Conversation(session, clock)
    c.begin()
    c.add_user('a')
    c.save()
    clock.t += 100
    c = Conversation(session, clock)
    c.begin()
    c.add_user('b')
    c.save()
    clock.t += 100  # 200 s after the first request, 100 s after the second
    assert len(Conversation(session, clock).messages) == 2


def test_refusal_is_not_kept(session):
    c = Conversation(session)
    c.begin()
    c.add_user('mach die bar auf')
    assert not c.add_answer('Das kann ich nicht.')
    c.save()
    assert session[conv.SESSION_KEY]['messages'] == [{'role': 'user', 'content': 'mach die bar auf'}]


def test_rollback_leaves_nothing_of_a_failed_request(session):
    c = Conversation(session)
    c.begin()
    c.add_user('a')
    c.add_answer('b')
    c.save()
    c.begin()
    c.add_user('c')
    c.add_call(ToolCall('bar_status', {}, 'c1'))
    c.rollback()
    c.save()
    assert session[conv.SESSION_KEY]['messages'] == [{'role': 'user', 'content': 'a'}, {'role': 'assistant', 'content': 'b'}]


def test_save_trims(session):
    c = Conversation(session)
    c.begin()
    for i in range(15):
        c.add_user('f%d' % i)
        c.add_answer('a%d' % i)
    c.save()
    messages = session[conv.SESSION_KEY]['messages']
    assert len(messages) == conv.MAX_MESSAGES
    assert messages[0]['role'] == 'user'


def test_pending_proposal_round_trip(session):
    c = Conversation(session)
    c.begin()
    c.add_user('mach eine durchsage: essen ist fertig')
    call = ToolCall('announce', {'text': 'essen ist fertig'}, 'c1')
    c.set_pending(call, 'durchsage: „essen ist fertig“')
    c.save()
    assert session[conv.SESSION_KEY]['messages'][-1] == call.message()

    c = Conversation(session)
    assert c.pending == {'id': 'c1', 'name': 'announce', 'arguments': {'text': 'essen ist fertig'}, 'description': 'durchsage: „essen ist fertig“'}
    assert c.pending_call() == call
    assert c.resolve_pending(True)['id'] == 'c1'
    assert c.pending is None
    assert c.pending_call() is None
    assert c.messages[-1] == {'role': 'tool', 'tool_call_id': 'c1', 'content': 'ausgeführt'}


def test_a_new_request_rejects_the_open_proposal(session):
    c = Conversation(session)
    c.begin()
    c.add_user('durchsage')
    c.set_pending(ToolCall('announce', {'text': 'x'}, 'c1'), 'durchsage: „x“')
    c.save()

    c = Conversation(session)
    c.begin()
    c.add_user('wer ist da?')
    assert c.pending is None
    assert c.messages[2] == {'role': 'tool', 'tool_call_id': 'c1', 'content': conv.REJECTED}
    # a failure of the new request keeps the rejection
    c.rollback()
    assert c.messages[-1]['content'] == conv.REJECTED
    assert len(c.messages) == 3


def test_resolve_without_pending_is_harmless(session):
    c = Conversation(session)
    assert c.resolve_pending(True) is None
    assert c.messages == []


def test_rollback_drops_a_proposal_made_in_the_failed_request(session):
    c = Conversation(session)
    c.begin()
    c.add_user('durchsage')
    c.set_pending(ToolCall('announce', {'text': 'x'}, 'c1'), 'durchsage: „x“')
    c.rollback()
    assert c.pending is None
    assert c.messages == []


@pytest.mark.django_db
def test_works_with_a_django_session():
    store = SessionStore()
    c = Conversation(store)
    c.begin()
    c.add_user('hallo')
    c.save()
    assert store.modified
    store.save()
    reloaded = SessionStore(session_key=store.session_key)
    assert Conversation(reloaded).messages == [{'role': 'user', 'content': 'hallo'}]
