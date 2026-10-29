"""
what the model may call (AI-ASSISTANT.md, section 7). the model only sees the
openai-style definitions and only ever proposes; every proposal is checked
parameter by parameter here before anything runs.

each tool has a fixed level the model cannot change:

  QUERY    runs at once, the result goes back to the model as a tool message
  SELF     runs at once because it only touches the user's own state
  CONFIRM  anything audible in the station: shown to the user, run on their tap

the station functions behind the tools are the same python the json-rpc
methods call, so nothing goes over the network except announce and play_sound
(c_out, the station's speakers). what the assistant says itself is spoken in
the browser, never over c_out.
"""

import logging
import re
import time
from dataclasses import dataclass, field, replace
from typing import Callable, Optional

import cbeamdcfg as cfg

from ..models import Mission
from ..views.audio import announce as rpc_announce, play as rpc_play, sounds as rpc_sounds
from ..views.auth import force_login, force_logout
from ..views.bar import get_barstatus
from ..views.events import event_list
from ..views.hardware import artefact_list
from ..views.helpers import userlist
from . import knowledge
from .chat import NOT_UNDERSTOOD, AssistantError, ToolCall

logger = logging.getLogger(__name__)

QUERY = 'query'
SELF = 'self'
CONFIRM = 'confirm'

DONE = "ausgeführt"
MAX_LINES = 60
DESCRIPTION_LENGTH = 160
# the sound list comes from shout; one lookup per minute is plenty
SOUNDS_TTL = 60


def normalize(text):
    """collapse all whitespace to single spaces."""
    return ' '.join(str(text).split())


def shorten(text, length):
    text = normalize(text)
    return text if len(text) <= length else text[:length - 1].rstrip() + '…'


def limit_lines(lines):
    """at most MAX_LINES lines, with "… und N weitere" at the end."""
    lines = list(lines)
    if len(lines) <= MAX_LINES:
        return '\n'.join(lines)
    rest = len(lines) - MAX_LINES
    return '\n'.join(lines[:MAX_LINES]) + '\n… und %d weitere' % rest


def quoted(text):
    return '„%s“' % text


@dataclass
class Param:
    description: str = ''
    required: bool = False
    max_length: Optional[int] = None
    enum: Optional[list] = None
    default: Optional[str] = None

    def schema(self):
        spec = {'type': 'string'}
        if self.description:
            spec['description'] = self.description
        if self.enum is not None:
            spec['enum'] = list(self.enum)
        return spec


@dataclass
class Tool:
    name: str
    level: str
    description: str
    run: Callable
    describe: Callable
    parameters: dict = field(default_factory=dict)
    # optional: turns validated arguments into what the tool runs with, e.g. a
    # sound's name into its file name; raises AssistantError when that fails
    resolve: Optional[Callable] = None

    def definition(self):
        """the tool in the openai function-calling format."""
        return {
            'type': 'function',
            'function': {
                'name': self.name,
                'description': self.description,
                'parameters': {
                    'type': 'object',
                    'properties': {name: p.schema() for name, p in self.parameters.items()},
                    'required': [name for name, p in self.parameters.items() if p.required],
                },
            },
        }

    def validate(self, arguments):
        """
        the arguments the tool will run with, or AssistantError when something
        the model sent does not fit. unknown keys are dropped, strings are
        whitespace-normalized and cut to max_length.
        """
        if not isinstance(arguments, dict):
            raise AssistantError(NOT_UNDERSTOOD)
        clean = {}
        for name, param in self.parameters.items():
            value = arguments.get(name)
            if value is None or (isinstance(value, str) and not value.strip()):
                if param.required:
                    raise AssistantError(NOT_UNDERSTOOD)
                if param.default is not None:
                    clean[name] = param.default
                continue
            if not isinstance(value, str):
                raise AssistantError(NOT_UNDERSTOOD)
            value = normalize(value)
            if param.max_length and len(value) > param.max_length:
                value = value[:param.max_length].rstrip()
            if param.enum is not None and value not in param.enum:
                raise AssistantError(NOT_UNDERSTOOD)
            clean[name] = value
        return clean


@dataclass
class Action:
    """a validated tool call, ready to run."""
    tool: Tool
    arguments: dict
    call_id: str

    @property
    def level(self):
        return self.tool.level

    @property
    def description(self):
        """what the user sees: progress line, confirmation, "ausgeführt"."""
        return self.tool.describe(self.arguments)

    def run(self, request):
        """the tool result for the model; station failures become AssistantErrors."""
        try:
            return self.tool.run(request, self.arguments)
        except AssistantError:
            raise
        except Exception:
            logger.exception("tool %s failed", self.tool.name)
            raise AssistantError("%s fehlgeschlagen" % self.description)


# the station functions behind the tools ---------------------------------------

def who_is_on_board(request, args):
    names = userlist()
    return ', '.join(names) if names else "niemand"


def bar_status(request, args):
    return "geöffnet" if get_barstatus(request) else "geschlossen"


def events_today(request, args):
    lines = []
    for event in event_list(request) or []:
        line = '%s (%s-%s)' % (normalize(event.get('title') or '-'), event.get('start', ''), event.get('end', ''))
        description = event.get('description')
        if description:
            line += ': ' + shorten(description, DESCRIPTION_LENGTH)
        lines.append(line)
    return limit_lines(lines) if lines else "keine events heute"


def missions(request, args):
    lines = []
    for mission in Mission.objects.order_by('-status', 'short_description'):
        line = '%s (%s, %d AP' % (normalize(mission.short_description), mission.status, mission.ap)
        assigned = [user.username for user in mission.assigned_to.all()]
        if assigned:
            line += ', übernommen von ' + ', '.join(assigned)
        lines.append(line + ')')
    return limit_lines(lines) if lines else "keine missionen"


def artefacts(request, args):
    search = args.get('search', '').lower()
    names = sorted(normalize(a['name']) for a in artefact_list(request) or [])
    hits = [name for name in names if search in name.lower()]
    if not hits:
        return "kein artefakt gefunden; für wissen über geräte und räume station_knowledge nutzen"
    return limit_lines(hits)


def station_knowledge(request, args):
    return knowledge.search(args['query'])


def login(request, args):
    force_login(request, request.user.username)
    return DONE


def logout(request, args):
    force_logout(request, request.user.username)
    return DONE


def announce(request, args):
    rpc_announce(request, args['text'])
    return DONE


def play_sound(request, args):
    rpc_play(request, args['sound'])
    return DONE


def _stem(name):
    return re.sub(r'\.[a-z0-9]+$', '', name.lower().strip())


def match_sound(wanted, names):
    """
    the file in names that wanted means: the exact name, else the same name
    without extension, else the first file whose name contains it. None when
    nothing fits.
    """
    wanted_stem = _stem(wanted)
    for fits in (lambda n: n.lower() == wanted.lower().strip(),
                 lambda n: _stem(n) == wanted_stem,
                 lambda n: wanted_stem and wanted_stem in _stem(n)):
        hits = sorted(n for n in names if fits(n))
        if hits:
            return hits[0]
    return None


def resolve_sound(args):
    found = match_sound(args['sound'], sound_names())
    if not found:
        raise AssistantError('sound %s nicht gefunden' % quoted(args['sound']))
    return {'sound': found}


# the tools ----------------------------------------------------------------------

WHO_IS_ON_BOARD = Tool(
    'who_is_on_board', QUERY,
    "Liste der Crewmitglieder, die gerade in der c-base eingeloggt sind",
    who_is_on_board, lambda a: "wer ist an bord")

BAR_STATUS = Tool(
    'bar_status', QUERY,
    "Ob die Bar der c-base gerade geöffnet ist",
    bar_status, lambda a: "bar-status")

EVENTS_TODAY = Tool(
    'events_today', QUERY,
    "Die heutigen Events und Veranstaltungen in der c-base",
    events_today, lambda a: "events")

MISSIONS = Tool(
    'missions', QUERY,
    "Die Missionen (Aufgaben) der c-base mit Status und AP",
    missions, lambda a: "missionen")

ARTEFACTS = Tool(
    'artefacts', QUERY,
    "Die Artefakte der c-base, also Räume, Geräte und Einrichtungen der Station",
    artefacts, lambda a: "artefakte: " + quoted(a['search']) if a.get('search') else "artefakte",
    {'search': Param("Optionaler Suchbegriff; leer für alle", max_length=200)})

STATION_KNOWLEDGE = Tool(
    'station_knowledge', QUERY,
    "Die Wissensdatenbank der c-base durchsuchen: Geschichte und Legende der Station, "
    "Räume, Technik, WLAN und Zugänge, Preise, Begriffe, Regeln, Projekte, Vereinsleben "
    "und Leute. Für jede Wissensfrage über die c-base",
    station_knowledge, lambda a: "suche: " + quoted(a['query']),
    {'query': Param("Suchanfrage auf Deutsch, als kurze Frage oder Stichworte", required=True, max_length=200)})

LOGIN = Tool(
    'login', SELF,
    "Den Nutzer in der c-base einloggen (an Bord melden)",
    login, lambda a: "einloggen")

LOGOUT = Tool(
    'logout', SELF,
    "Den Nutzer aus der c-base ausloggen (von Bord melden)",
    logout, lambda a: "ausloggen")

ANNOUNCE = Tool(
    'announce', CONFIRM,
    "Eine Durchsage über die Lautsprecher der Station machen",
    announce, lambda a: "durchsage: " + quoted(a['text']),
    {'text': Param("Der Text der Durchsage", required=True, max_length=200)})

# the sound's name is a free string on purpose: offered as an enum of the 156
# file names, the model stopped calling any tool at all (checked 2026-10-29
# against gemma4:e4b: five of eight station questions were answered from thin
# air). the name is matched against shout's list before the confirmation.
PLAY_SOUND = Tool(
    'play_sound', CONFIRM,
    "Einen Sound über die Lautsprecher der Station abspielen",
    play_sound, lambda a: "sound: " + a['sound'],
    {'sound': Param("Name oder Stichwort des Sounds, zum Beispiel laserraycannon oder siri",
                    required=True, max_length=100)},
    resolve=resolve_sound)


_sounds_cache = (0.0, [])


def sound_names():
    """the sound files shout can play, cached for SOUNDS_TTL seconds."""
    global _sounds_cache
    fetched, names = _sounds_cache
    now = time.monotonic()
    if now - fetched < SOUNDS_TTL:
        return names
    try:
        names = [str(name) for name in rpc_sounds(None) or []]
    except Exception:
        logger.exception("sound list unavailable")
        names = []
    _sounds_cache = (now, names)
    return names


def available(username=None):
    """
    the tools the model gets to see right now. station_knowledge needs a
    configured knowledge base (RAG_URL and RAG_KEY), play_sound a sound list; username only shapes the
    description of login ("einloggen als smile").
    """
    tools = [WHO_IS_ON_BOARD, BAR_STATUS, EVENTS_TODAY, MISSIONS, ARTEFACTS]
    if knowledge.configured():
        tools.append(STATION_KNOWLEDGE)
    if username:
        tools.append(replace(LOGIN, describe=lambda a: "einloggen als " + username))
    else:
        tools.append(LOGIN)
    tools.append(LOGOUT)
    tools.append(ANNOUNCE)
    if sound_names():
        tools.append(PLAY_SOUND)
    return tools


def definitions(tools):
    return [tool.definition() for tool in tools]


def names(tools):
    return {tool.name for tool in tools}


def prepare(tools, call: ToolCall):
    """an Action for the model's proposal, or AssistantError("nicht verstanden")."""
    for tool in tools:
        if tool.name == call.name:
            arguments = tool.validate(call.arguments)
            if tool.resolve:
                arguments = tool.resolve(arguments)
            return Action(tool, arguments, call.id)
    raise AssistantError(NOT_UNDERSTOOD)
