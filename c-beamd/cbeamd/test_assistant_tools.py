"""
tests for cbeamd.assistant.tools: the registry, the validation of what the
model proposes, and the station functions behind each tool.
"""

from datetime import timedelta
from unittest import mock

import pytest
from django.contrib.auth import get_user_model
from django.test import RequestFactory
from django.utils import timezone

import cbeamdcfg as cfg
from cbeamd.assistant import tools
from cbeamd.assistant.chat import AssistantError, ToolCall
from cbeamd.assistant.tools import CONFIRM, QUERY, SELF, Param, Tool
from cbeamd.models import Mission, Status, User


@pytest.fixture(autouse=True)
def no_knowledge_no_sounds(monkeypatch):
    monkeypatch.setattr(cfg, 'rag_key', '')
    monkeypatch.setattr(tools, '_sounds_cache', (0.0, []))
    with mock.patch('cbeamd.assistant.tools.rpc_sounds', return_value=[]):
        yield


@pytest.fixture
def request_as_smile(db, settings):
    settings.PASSWORD_HASHERS = ['django.contrib.auth.hashers.MD5PasswordHasher']
    request = RequestFactory().post('/assistant/ask')
    request.user = get_user_model().objects.create_user('smile', password='pw')
    return request


def crew(username, status='online'):
    now = timezone.now()
    return User.objects.create(username=username, status=status, logintime=now, logouttime=now - timedelta(hours=2))


def by_name(name, username=None):
    return next(t for t in tools.available(username) if t.name == name)


def prepared(name, arguments=None, username=None):
    return tools.prepare(tools.available(username), ToolCall(name, arguments or {}, 'call_1'))


# definitions ----------------------------------------------------------------------

def test_definition_is_in_the_openai_format():
    assert tools.ANNOUNCE.definition() == {
        'type': 'function',
        'function': {
            'name': 'announce',
            'description': "Eine Durchsage über die Lautsprecher der Station machen",
            'parameters': {
                'type': 'object',
                'properties': {'text': {'type': 'string', 'description': "Der Text der Durchsage"}},
                'required': ['text'],
            },
        },
    }


def test_levels_are_fixed_per_tool():
    levels = {t.name: t.level for t in tools.available()}
    assert levels == {
        'who_is_on_board': QUERY, 'bar_status': QUERY, 'events_today': QUERY,
        'missions': QUERY, 'artefacts': QUERY,
        'login': SELF, 'logout': SELF, 'announce': CONFIRM,
    }


def test_station_knowledge_is_offered_only_with_a_key(monkeypatch):
    assert 'station_knowledge' not in tools.names(tools.available())
    monkeypatch.setattr(cfg, 'rag_key', 'secret')
    assert 'station_knowledge' in tools.names(tools.available())


def test_play_sound_is_offered_with_a_free_name_not_an_enum():
    with mock.patch('cbeamd.assistant.tools.rpc_sounds', return_value=['beep.mp3', 'siri.mp3']):
        tool = by_name('play_sound')
    assert tool.level == CONFIRM
    assert 'enum' not in tool.definition()['function']['parameters']['properties']['sound']


def test_sound_list_is_cached(monkeypatch):
    with mock.patch('cbeamd.assistant.tools.rpc_sounds', return_value=['a.mp3']) as rpc:
        assert tools.sound_names() == ['a.mp3']
        assert tools.sound_names() == ['a.mp3']
        assert rpc.call_count == 1


def test_sound_list_failure_means_no_tool():
    with mock.patch('cbeamd.assistant.tools.rpc_sounds', side_effect=RuntimeError('shout down')):
        assert 'play_sound' not in tools.names(tools.available())


def test_login_description_names_the_user():
    assert by_name('login', 'smile').describe({}) == 'einloggen als smile'
    assert by_name('login').describe({}) == 'einloggen'


# validation -----------------------------------------------------------------------

def test_unknown_tool_is_not_understood():
    with pytest.raises(AssistantError, match='nicht verstanden'):
        prepared('say', {'text': 'hallo'})


def test_missing_required_argument_is_not_understood():
    for arguments in ({}, {'text': ''}, {'text': '   '}, {'text': None}):
        with pytest.raises(AssistantError, match='nicht verstanden'):
            prepared('announce', arguments)


def test_non_string_argument_is_not_understood():
    with pytest.raises(AssistantError, match='nicht verstanden'):
        prepared('announce', {'text': 42})


def test_value_outside_enum_is_not_understood():
    tool = Tool('t', QUERY, 'd', lambda r, a: a, lambda a: 't', {'voice': Param(enum=['julia', 'r2d2'])})
    with pytest.raises(AssistantError, match='nicht verstanden'):
        tool.validate({'voice': 'c3po'})


SOUNDS = ['siri.mp3', 'siri_looped.mp3', 'laserraycannon.mp3', 'Cultur.mp3', '281395_SOUNDDOGS__sp.mp3']


@pytest.mark.parametrize('wanted, expected', [
    ('siri.mp3', 'siri.mp3'),
    ('siri', 'siri.mp3'),
    ('Siri', 'siri.mp3'),
    ('siri looped', None),
    ('siri_looped', 'siri_looped.mp3'),
    ('laser', 'laserraycannon.mp3'),
    ('cultur', 'Cultur.mp3'),
    ('sounddogs', '281395_SOUNDDOGS__sp.mp3'),
    ('fräse', None),
    ('', None),
])
def test_sound_names_are_matched_against_the_list(wanted, expected):
    assert tools.match_sound(wanted, SOUNDS) == expected


def test_play_sound_resolves_the_name_before_the_confirmation():
    with mock.patch('cbeamd.assistant.tools.rpc_sounds', return_value=SOUNDS):
        action = prepared('play_sound', {'sound': 'laser'})
        assert action.arguments == {'sound': 'laserraycannon.mp3'}
        assert action.description == 'sound: laserraycannon.mp3'
        with pytest.raises(AssistantError, match='sound „fräse“ nicht gefunden'):
            prepared('play_sound', {'sound': 'fräse'})


def test_arguments_are_normalized_cut_and_unknown_keys_dropped():
    action = prepared('announce', {'text': '  hallo \n  welt ' + 'x' * 300, 'volume': 'loud'})
    assert action.arguments == {'text': ('hallo welt ' + 'x' * 300)[:200]}
    assert action.call_id == 'call_1'
    assert action.level == CONFIRM
    assert action.description == 'durchsage: „%s“' % action.arguments['text']


def test_optional_argument_may_be_absent():
    assert prepared('artefacts').arguments == {}
    assert prepared('artefacts', {'search': 'bar'}).arguments == {'search': 'bar'}


def test_default_fills_an_absent_optional_argument():
    tool = Tool('t', QUERY, 'd', lambda r, a: a, lambda a: 't', {'voice': Param(default='julia', enum=['julia', 'r2d2'])})
    assert tool.validate({}) == {'voice': 'julia'}
    assert tool.validate({'voice': 'r2d2'}) == {'voice': 'r2d2'}


def test_non_dict_arguments_are_not_understood():
    with pytest.raises(AssistantError, match='nicht verstanden'):
        tools.ANNOUNCE.validate(['hallo'])


# running --------------------------------------------------------------------------

def test_station_failure_becomes_an_assistant_error(request_as_smile):
    with mock.patch('cbeamd.assistant.tools.userlist', side_effect=RuntimeError('db gone')):
        with pytest.raises(AssistantError, match='wer ist an bord fehlgeschlagen'):
            prepared('who_is_on_board').run(request_as_smile)


def test_assistant_errors_pass_through(request_as_smile, monkeypatch):
    monkeypatch.setattr(cfg, 'rag_key', 'secret')
    with mock.patch('cbeamd.assistant.tools.knowledge.search', side_effect=AssistantError('wissensdatenbank: zugriff verweigert')):
        with pytest.raises(AssistantError, match='zugriff verweigert'):
            prepared('station_knowledge', {'query': 'wlan'}).run(request_as_smile)


@pytest.mark.django_db
def test_who_is_on_board(request_as_smile):
    assert prepared('who_is_on_board').run(request_as_smile) == 'niemand'
    crew('zed')
    crew('alice')
    crew('bob', status='offline')
    assert prepared('who_is_on_board').run(request_as_smile) == 'alice, zed'


@pytest.mark.django_db
def test_bar_status(request_as_smile):
    Status.objects.create(bar_open=False)
    assert prepared('bar_status').run(request_as_smile) == 'geschlossen'
    Status.objects.update(bar_open=True)
    assert prepared('bar_status').run(request_as_smile) == 'geöffnet'


def test_events_today(request_as_smile):
    events = [
        {'title': 'c++ user  group', 'start': '1900', 'end': '2200', 'description': 'x' * 200},
        {'title': 'stammtisch', 'start': '2000', 'end': '2300', 'description': None},
    ]
    with mock.patch('cbeamd.assistant.tools.event_list', return_value=events):
        result = prepared('events_today').run(request_as_smile)
    lines = result.split('\n')
    assert lines[0] == 'c++ user group (1900-2200): ' + 'x' * 159 + '…'
    assert lines[1] == 'stammtisch (2000-2300)'
    with mock.patch('cbeamd.assistant.tools.event_list', return_value=[]):
        assert prepared('events_today').run(request_as_smile) == 'keine events heute'


@pytest.mark.django_db
def test_missions(request_as_smile):
    assert prepared('missions').run(request_as_smile) == 'keine missionen'
    m = Mission.objects.create(short_description='bar putzen', description='', status='open', ap=3)
    m.assigned_to.add(crew('alice'), crew('bob'))
    Mission.objects.create(short_description='müll raus', description='', status='completed', ap=1)
    assert prepared('missions').run(request_as_smile) == (
        'bar putzen (open, 3 AP, übernommen von alice, bob)\n'
        'müll raus (completed, 1 AP)')


def test_artefacts(request_as_smile):
    artefacts = [{'name': 'Matelight', 'slug': 'matelight'}, {'name': 'Bar', 'slug': 'bar'}, {'name': 'c-lab', 'slug': 'c-lab'}]
    with mock.patch('cbeamd.assistant.tools.artefact_list', return_value=artefacts):
        assert prepared('artefacts').run(request_as_smile) == 'Bar\nMatelight\nc-lab'
        assert prepared('artefacts', {'search': 'mate'}).run(request_as_smile) == 'Matelight'
        assert prepared('artefacts', {'search': 'fräse'}).run(request_as_smile) == (
            'kein artefakt gefunden; für wissen über geräte und räume station_knowledge nutzen')
    assert prepared('artefacts', {'search': 'mate'}).description == 'artefakte: „mate“'


def test_long_lists_are_cut(request_as_smile):
    artefacts = [{'name': 'a%03d' % i, 'slug': ''} for i in range(75)]
    with mock.patch('cbeamd.assistant.tools.artefact_list', return_value=artefacts):
        result = prepared('artefacts').run(request_as_smile)
    lines = result.split('\n')
    assert len(lines) == 61
    assert lines[-1] == '… und 15 weitere'


def test_station_knowledge_passes_the_query(request_as_smile, monkeypatch):
    monkeypatch.setattr(cfg, 'rag_key', 'secret')
    with mock.patch('cbeamd.assistant.tools.knowledge.search', return_value='[quelle]\ntext') as search:
        action = prepared('station_knowledge', {'query': ' wlan  passwort '})
        assert action.run(request_as_smile) == '[quelle]\ntext'
    search.assert_called_once_with('wlan passwort')
    assert action.description == 'suche: „wlan passwort“'


def test_login_and_logout_act_on_the_session_user(request_as_smile):
    with mock.patch('cbeamd.assistant.tools.force_login') as login, mock.patch('cbeamd.assistant.tools.force_logout') as logout:
        assert prepared('login', username='smile').run(request_as_smile) == 'ausgeführt'
        assert prepared('logout').run(request_as_smile) == 'ausgeführt'
    login.assert_called_once_with(request_as_smile, 'smile')
    logout.assert_called_once_with(request_as_smile, 'smile')


def test_announce_goes_over_c_out(request_as_smile):
    with mock.patch('cbeamd.assistant.tools.rpc_announce') as rpc:
        action = prepared('announce', {'text': 'die bar ist offen'})
        assert action.level == CONFIRM
        assert action.run(request_as_smile) == 'ausgeführt'
    rpc.assert_called_once_with(request_as_smile, 'die bar ist offen')


def test_play_sound_goes_over_c_out(request_as_smile):
    with mock.patch('cbeamd.assistant.tools.rpc_sounds', return_value=['siri.mp3']), \
            mock.patch('cbeamd.assistant.tools.rpc_play') as rpc:
        action = prepared('play_sound', {'sound': 'siri.mp3'})
        assert action.description == 'sound: siri.mp3'
        assert action.run(request_as_smile) == 'ausgeführt'
    rpc.assert_called_once_with(request_as_smile, 'siri.mp3')
