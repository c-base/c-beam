"""
the knowledge base behind station_knowledge (AI-ASSISTANT.md, section 9.1):
qdrant, spoken to directly. qdrant has no question endpoint, only vectors, so
a search is three steps, the first of them once per process:

1. the collection's layout: vector size, and the vector's name when the
   collection uses named vectors.
2. the question embedded on the ai server. nomic v1 insists on the
   "search_query: " prefix; the chunks were embedded with the matching
   document prefix.
3. the nearest chunks, above a score threshold. the scores are squashed: a
   fitting chunk sits around 0.55, generic hub pages around 0.36 to 0.41,
   hence the threshold, and the note to the model that the hits are only
   candidates. without that note it once invented a cnc mill out of chunks
   about the server landscape.

the result is the text the model gets as the tool's result. the api key stays
on the server; the browser never sees qdrant.
"""

import logging

import requests

import cbeamdcfg as cfg

from . import chat
from .chat import AssistantError

logger = logging.getLogger(__name__)

QUERY_PREFIX = 'search_query: '
LIMIT = 5
SCORE_THRESHOLD = 0.40
CHUNK_LENGTH = 700
SOURCE_LENGTH = 80
READ_TIMEOUT = 30

TEXT_FIELDS = ('text', 'content', 'page_content', 'chunk', 'document', 'body')
SOURCE_FIELDS = ('title', 'source', 'url', 'file', 'path', 'name')

HEADER = ("Fundstellen der Ähnlichkeitssuche, die passendste zuerst; unpassende ignorieren, "
          "nichts hinzuerfinden:")
NOTHING = ("nichts gefunden: die wissensdatenbank enthält nichts dazu. sage das und verweise auf "
           "die datenrettungssonde siri, die diese information leider auch nicht enthält")
UNREACHABLE = "wissensdatenbank nicht erreichbar"

# collection layouts by (url, collection): {'size': int, 'using': name or None}
_layouts = {}


def configured():
    return bool(cfg.rag_url and cfg.rag_key)


def reset_cache():
    _layouts.clear()


def _url(path):
    return cfg.rag_url.rstrip('/') + '/' + path.lstrip('/')


def _request(method, path, json=None):
    """one call to qdrant; http errors become the terminal's messages."""
    try:
        response = requests.request(
            method, _url(path), json=json, headers={'api-key': cfg.rag_key},
            timeout=(cfg.ai_connect_timeout, READ_TIMEOUT))
    except requests.Timeout:
        raise AssistantError("wissensdatenbank antwortet nicht")
    except requests.RequestException as e:
        logger.warning("qdrant request failed: %s", e)
        raise AssistantError(UNREACHABLE)
    if response.status_code in (401, 403):
        raise AssistantError("wissensdatenbank: zugriff verweigert, api-key prüfen")
    if response.status_code == 404:
        raise AssistantError("wissensdatenbank: collection nicht gefunden")
    if not response.ok:
        logger.warning("qdrant answered %s: %s", response.status_code, response.text[:200])
        raise AssistantError("wissensdatenbank: HTTP %d" % response.status_code)
    try:
        return response.json()
    except ValueError:
        raise AssistantError("wissensdatenbank: unlesbare antwort")


def layout():
    """
    {'size': vector size, 'using': vector name or None} of the collection. with
    named vectors the first dense one (the first with a size) is used, and its
    name goes into the search as `using`.
    """
    key = (cfg.rag_url, cfg.rag_collection)
    if key in _layouts:
        return _layouts[key]
    data = _request('GET', 'collections/%s' % cfg.rag_collection)
    try:
        vectors = data['result']['config']['params']['vectors']
    except (KeyError, TypeError):
        raise AssistantError("wissensdatenbank: unlesbare antwort")
    found = None
    if isinstance(vectors, dict) and isinstance(vectors.get('size'), int):
        found = {'size': vectors['size'], 'using': None}
    elif isinstance(vectors, dict):
        for name, spec in vectors.items():
            if isinstance(spec, dict) and isinstance(spec.get('size'), int):
                found = {'size': spec['size'], 'using': name}
                break
    if found is None:
        raise AssistantError("wissensdatenbank: collection ohne dichten vektor")
    _layouts[key] = found
    return found


def embed(question):
    """the question's vector from the ai server."""
    data = chat.post('embeddings', json={'model': cfg.ai_embed_model, 'input': QUERY_PREFIX + question})
    try:
        vector = data['data'][0]['embedding']
    except (KeyError, IndexError, TypeError):
        raise AssistantError("KI-server: unlesbare antwort")
    if not isinstance(vector, list) or not vector:
        raise AssistantError("KI-server: unlesbare antwort")
    return vector


def query_points(vector, using):
    body = {
        'query': vector,
        'limit': LIMIT,
        'score_threshold': SCORE_THRESHOLD,
        'with_payload': True,
        'with_vector': False,
    }
    if using:
        body['using'] = using
    data = _request('POST', 'collections/%s/points/query' % cfg.rag_collection, json=body)
    try:
        points = data['result']['points']
    except (KeyError, TypeError):
        raise AssistantError("wissensdatenbank: unlesbare antwort")
    return points if isinstance(points, list) else []


# payload reading -------------------------------------------------------------------

def _first_string(mapping, fields):
    for name in fields:
        value = mapping.get(name)
        if isinstance(value, str) and value.strip():
            return value
    return None


def chunk_text(payload):
    """the text of a chunk: a known field, else the longest string in the payload."""
    if not isinstance(payload, dict):
        return ''
    text = _first_string(payload, TEXT_FIELDS)
    if text is None:
        strings = [v for v in payload.values() if isinstance(v, str)]
        for nested in payload.values():
            if isinstance(nested, dict):
                strings += [v for v in nested.values() if isinstance(v, str)]
        text = max(strings, key=len) if strings else ''
    return ' '.join(text.split())


def chunk_source(payload):
    """where a chunk came from, from the payload or its metadata, or None."""
    if not isinstance(payload, dict):
        return None
    source = _first_string(payload, SOURCE_FIELDS)
    metadata = payload.get('metadata')
    if source is None and isinstance(metadata, dict):
        source = _first_string(metadata, SOURCE_FIELDS)
    if source is None:
        return None
    source = ' '.join(source.split())
    return source if len(source) <= SOURCE_LENGTH else source[:SOURCE_LENGTH - 1].rstrip() + '…'


def format_hits(points):
    """the tool result for the model, or the nothing-found text."""
    blocks = []
    for number, point in enumerate(points, 1):
        payload = point.get('payload') if isinstance(point, dict) else None
        text = chunk_text(payload)
        if not text:
            continue
        if len(text) > CHUNK_LENGTH:
            text = text[:CHUNK_LENGTH - 1].rstrip() + '…'
        source = chunk_source(payload) or 'fundstelle %d' % number
        blocks.append('[%s]\n%s' % (source, text))
    if not blocks:
        return NOTHING
    return HEADER + '\n\n' + '\n\n'.join(blocks)


def search(question):
    """the tool result of station_knowledge for question."""
    if not configured():
        raise AssistantError("wissensdatenbank nicht konfiguriert")
    shape = layout()
    vector = embed(question)
    if len(vector) != shape['size']:
        raise AssistantError("wissensdatenbank: vektorgröße %d passt nicht zur collection (%d)"
                             % (len(vector), shape['size']))
    return format_hits(query_points(vector, shape['using']))
