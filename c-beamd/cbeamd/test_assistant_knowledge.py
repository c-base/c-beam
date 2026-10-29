"""
tests for cbeamd.assistant.knowledge: the qdrant search behind
station_knowledge, against a mocked qdrant and a mocked embedding endpoint.
"""

import json
from unittest import mock

import pytest
import requests

import cbeamdcfg as cfg
from cbeamd.assistant import knowledge
from cbeamd.assistant.chat import AssistantError


class FakeResponse:
    def __init__(self, status=200, body=None):
        self.status_code = status
        self.ok = status < 400
        self._body = body
        self.text = json.dumps(body) if body is not None else ''

    def json(self):
        if self._body is None:
            raise ValueError("no json")
        return self._body


def collection(vectors):
    return FakeResponse(body={'result': {'config': {'params': {'vectors': vectors}}}})


def points(*hits):
    return FakeResponse(body={'result': {'points': list(hits)}})


def hit(payload, score=0.55):
    return {'id': 1, 'score': score, 'payload': payload}


VECTOR = [0.1] * 768


@pytest.fixture(autouse=True)
def configured(monkeypatch):
    monkeypatch.setattr(cfg, 'ai_url', 'http://ai.test/v1/')
    monkeypatch.setattr(cfg, 'ai_embed_model', 'nomic-test')
    monkeypatch.setattr(cfg, 'ai_connect_timeout', 5)
    monkeypatch.setattr(cfg, 'ai_read_timeout', 60)
    monkeypatch.setattr(cfg, 'rag_url', 'http://qdrant.test:8123/')
    monkeypatch.setattr(cfg, 'rag_key', 'secret')
    monkeypatch.setattr(cfg, 'rag_collection', 'cbase_knowledge')
    knowledge.reset_cache()


@pytest.fixture
def qdrant():
    with mock.patch('cbeamd.assistant.knowledge.requests.request') as m:
        yield m


@pytest.fixture
def embedding():
    with mock.patch('cbeamd.assistant.knowledge.chat.post', return_value={'data': [{'embedding': VECTOR}]}) as m:
        yield m


# the three steps ----------------------------------------------------------------------

def test_search_runs_layout_embedding_and_query(qdrant, embedding):
    qdrant.side_effect = [
        collection({'size': 768, 'distance': 'Cosine'}),
        points(hit({'text': 'Das Crew-WLAN heißt c-base-crew.', 'title': 'WLAN'})),
    ]
    result = knowledge.search('wlan passwort')
    assert result == knowledge.HEADER + '\n\n[WLAN]\nDas Crew-WLAN heißt c-base-crew.'

    layout_call, query_call = qdrant.call_args_list
    assert layout_call.args == ('GET', 'http://qdrant.test:8123/collections/cbase_knowledge')
    assert layout_call.kwargs['headers'] == {'api-key': 'secret'}
    assert layout_call.kwargs['timeout'] == (5, knowledge.READ_TIMEOUT)

    embedding.assert_called_once_with('embeddings', json={'model': 'nomic-test', 'input': 'search_query: wlan passwort'})

    assert query_call.args == ('POST', 'http://qdrant.test:8123/collections/cbase_knowledge/points/query')
    assert query_call.kwargs['json'] == {
        'query': VECTOR, 'limit': 5, 'score_threshold': 0.40, 'with_payload': True, 'with_vector': False}


def test_named_vectors_use_the_first_dense_one(qdrant, embedding):
    qdrant.side_effect = [
        collection({'sparse': {'modifier': 'idf'}, 'dense': {'size': 768}, 'other': {'size': 1024}}),
        points(),
    ]
    assert knowledge.search('x') == knowledge.NOTHING
    assert qdrant.call_args_list[1].kwargs['json']['using'] == 'dense'


def test_layout_is_read_once(qdrant, embedding):
    qdrant.side_effect = [collection({'size': 768}), points(), points()]
    knowledge.search('a')
    knowledge.search('b')
    assert [c.args[0] for c in qdrant.call_args_list] == ['GET', 'POST', 'POST']


def test_layout_is_per_collection(qdrant, embedding, monkeypatch):
    qdrant.side_effect = [collection({'size': 768}), points(), collection({'size': 768}), points()]
    knowledge.search('a')
    monkeypatch.setattr(cfg, 'rag_collection', 'other')
    knowledge.search('a')
    assert qdrant.call_count == 4


def test_vector_size_mismatch_is_a_configuration_error(qdrant, embedding):
    qdrant.return_value = collection({'size': 1024})
    with pytest.raises(AssistantError, match='vektorgröße 768 passt nicht zur collection \\(1024\\)'):
        knowledge.search('x')
    assert qdrant.call_count == 1


def test_collection_without_dense_vector(qdrant, embedding):
    qdrant.return_value = collection({'sparse': {'modifier': 'idf'}})
    with pytest.raises(AssistantError, match='ohne dichten vektor'):
        knowledge.search('x')


def test_unconfigured_knowledge_base(qdrant, embedding, monkeypatch):
    monkeypatch.setattr(cfg, 'rag_key', '')
    assert not knowledge.configured()
    with pytest.raises(AssistantError, match='nicht konfiguriert'):
        knowledge.search('x')
    qdrant.assert_not_called()


# qdrant errors --------------------------------------------------------------------------

@pytest.mark.parametrize('status, message', [
    (401, 'zugriff verweigert, api-key prüfen'),
    (403, 'zugriff verweigert, api-key prüfen'),
    (404, 'collection nicht gefunden'),
    (500, 'HTTP 500'),
])
def test_http_errors(qdrant, embedding, status, message):
    qdrant.return_value = FakeResponse(status, body={'status': {'error': 'x'}})
    with pytest.raises(AssistantError, match=message):
        knowledge.search('x')


def test_timeout_and_connection_errors(qdrant, embedding):
    qdrant.side_effect = requests.Timeout()
    with pytest.raises(AssistantError, match='antwortet nicht'):
        knowledge.search('x')
    qdrant.side_effect = requests.ConnectionError()
    with pytest.raises(AssistantError, match='nicht erreichbar'):
        knowledge.search('x')


def test_unreadable_answers(qdrant, embedding):
    qdrant.return_value = FakeResponse(body=None)
    with pytest.raises(AssistantError, match='unlesbare antwort'):
        knowledge.search('x')
    qdrant.return_value = FakeResponse(body={'result': {}})
    with pytest.raises(AssistantError, match='unlesbare antwort'):
        knowledge.search('x')


def test_unreadable_embedding(qdrant):
    qdrant.return_value = collection({'size': 768})
    with mock.patch('cbeamd.assistant.knowledge.chat.post', return_value={'data': []}):
        with pytest.raises(AssistantError, match='KI-server: unlesbare antwort'):
            knowledge.search('x')


def test_embedding_errors_pass_through(qdrant):
    qdrant.return_value = collection({'size': 768})
    with mock.patch('cbeamd.assistant.knowledge.chat.post', side_effect=AssistantError('KI-server ausgelastet')):
        with pytest.raises(AssistantError, match='ausgelastet'):
            knowledge.search('x')


# reading chunks ------------------------------------------------------------------------

def test_text_field_order():
    assert knowledge.chunk_text({'content': 'b', 'text': 'a'}) == 'a'
    assert knowledge.chunk_text({'page_content': 'c', 'content': 'b'}) == 'b'
    assert knowledge.chunk_text({'body': 'f', 'document': 'e'}) == 'e'
    assert knowledge.chunk_text({'text': '  a \n b  '}) == 'a b'


def test_text_falls_back_to_the_longest_string():
    payload = {'id': 'x', 'summary': 'kurz', 'metadata': {'raw': 'der längste string im payload'}, 'n': 3}
    assert knowledge.chunk_text(payload) == 'der längste string im payload'
    assert knowledge.chunk_text({'n': 3}) == ''
    assert knowledge.chunk_text(None) == ''


def test_source_fields_and_metadata():
    assert knowledge.chunk_source({'title': 'WLAN', 'source': 'wiki'}) == 'WLAN'
    assert knowledge.chunk_source({'metadata': {'source': 'wiki/wlan.md'}}) == 'wiki/wlan.md'
    assert knowledge.chunk_source({'metadata': {'path': 'p'}, 'url': 'u'}) == 'u'
    assert knowledge.chunk_source({'text': 'x'}) is None
    long = 'https://wiki.c-base.org/' + 'a' * 100
    source = knowledge.chunk_source({'url': long})
    assert len(source) == knowledge.SOURCE_LENGTH and source.endswith('…')


def test_format_hits_cuts_chunks_and_numbers_sourceless_ones():
    result = knowledge.format_hits([
        hit({'text': 'x' * 800, 'title': 'lang'}),
        hit({'text': 'ohne quelle'}),
        hit({'other': 42}),
    ])
    blocks = result.split('\n\n')
    assert blocks[0] == knowledge.HEADER
    assert blocks[1].startswith('[lang]\n')
    assert len(blocks[1]) == len('[lang]\n') + knowledge.CHUNK_LENGTH
    assert blocks[1].endswith('…')
    assert blocks[2] == '[fundstelle 2]\nohne quelle'
    assert len(blocks) == 3


def test_format_hits_without_usable_hits():
    assert knowledge.format_hits([]) == knowledge.NOTHING
    assert knowledge.format_hits([hit({'n': 1})]) == knowledge.NOTHING
    assert knowledge.format_hits(['garbage']) == knowledge.NOTHING
