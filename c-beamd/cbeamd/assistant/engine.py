"""
one request to the assistant, start to finish (AI-ASSISTANT.md, section 2):
the text goes into the conversation, the model answers in words or with a
tool call, QUERY tools feed their result back to the model, SELF tools run,
CONFIRM tools wait for the user. at most three rounds per request; in the
third, a tool result is shown as the answer.

the result is a Reply: the lines for the terminal, what to read aloud, and the
open proposal, if any. the views only turn that into json.
"""

import logging
from dataclasses import dataclass, field
from typing import Optional

# tools imports the station functions from cbeamd.views, whose package init
# imports the assistant views, which import this module: when tools is the
# first thing imported, it is only half there at this point. the module
# reference is fine (its attributes are read at call time), names from it are not.
from . import chat, prompt, tools
from .chat import AssistantError
from .conversation import Conversation

logger = logging.getLogger(__name__)

MAX_ROUNDS = 3
SPOKEN_DONE = "Erledigt."
SPOKEN_CONFIRM = "%s. Ausführen?"


@dataclass
class Reply:
    """what the terminal shows for one request; each line has a kind and a text."""
    lines: list = field(default_factory=list)
    speak: Optional[str] = None
    confirm: Optional[dict] = None

    def add(self, kind, text):
        self.lines.append({'kind': kind, 'text': text})
        return self

    @staticmethod
    def error(text):
        return Reply().add('error', 'fehler: ' + text)


def terminal(text):
    """the c-base writes everything in lower case."""
    return text.lower()


def _system(request, voice, offered):
    knowledge = 'station_knowledge' in tools.names(offered)
    return prompt.system_message(request.user.username, knowledge=knowledge, voice=voice)


def _run_recorded(request, conv, action, call):
    """run a tool and put call and result into the conversation."""
    result = action.run(request)
    conv.add_call(call)
    conv.add_result(call.id, result)
    return result


def ask(request, text, voice=False):
    """
    answer one user utterance. the conversation lives in request.session; a
    failure leaves nothing of this request behind.
    """
    text = ' '.join((text or '').split())
    if not text:
        return Reply.error("nichts verstanden")
    if not chat.configured():
        return Reply.error("KI-server nicht konfiguriert")
    conv = Conversation(request.session)
    conv.begin()
    conv.add_user(text)
    try:
        reply = _rounds(request, conv, voice)
    except AssistantError as e:
        conv.rollback()
        conv.save()
        return Reply.error(str(e))
    except Exception:
        logger.exception("assistant request failed")
        conv.rollback()
        conv.save()
        return Reply.error("interner fehler")
    conv.save()
    return reply


def _rounds(request, conv, voice):
    offered = tools.available(request.user.username)
    definitions = tools.definitions(offered)
    for round_number in range(1, MAX_ROUNDS + 1):
        messages = [_system(request, voice, offered)] + conv.messages
        answer = chat.complete(messages, definitions)
        if answer.text is not None:
            conv.add_answer(answer.text)
            return Reply(speak=answer.text).add('answer', terminal(answer.text))
        call = answer.tool_call
        action = tools.prepare(offered, call)
        if action.level == tools.CONFIRM:
            conv.set_pending(call, action.description)
            reply = Reply(speak=SPOKEN_CONFIRM % action.description)
            reply.confirm = {'id': call.id, 'description': action.description}
            return reply.add('confirm', '%s [j/n]' % action.description)
        if action.level == tools.SELF:
            _run_recorded(request, conv, action, call)
            return Reply(speak=SPOKEN_DONE).add('done', 'ausgefu:hrt: ' + action.description)
        result = _run_recorded(request, conv, action, call)
        if round_number == MAX_ROUNDS:
            # the model keeps calling tools; show what the last one found
            return Reply(speak=result).add('answer', terminal(result))
    raise AssistantError("keine antwort")  # unreachable: the loop always returns


def confirm(request, call_id, accept):
    """the user's decision on the open proposal."""
    conv = Conversation(request.session)
    pending = conv.pending
    if not pending or pending['id'] != call_id:
        return Reply.error("kein offener vorschlag")
    conv.touch()
    if not accept:
        conv.resolve_pending(False)
        conv.save()
        return Reply().add('info', 'verworfen: ' + pending['description'])
    try:
        action = tools.prepare(tools.available(request.user.username), conv.pending_call())
        action.run(request)
    except AssistantError as e:
        conv.resolve_pending(False)
        conv.save()
        return Reply.error(str(e))
    except Exception:
        logger.exception("confirmed action failed")
        conv.resolve_pending(False)
        conv.save()
        return Reply.error("interner fehler")
    conv.resolve_pending(True)
    conv.save()
    return Reply(speak=SPOKEN_DONE).add('done', 'ausgefu:hrt: ' + pending['description'])
