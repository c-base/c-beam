"""
the conversation (AI-ASSISTANT.md, section 8): the chat history that lets the
user ask follow-ups ("und in Fuß?"), kept in the django session.

rules, all of them learned the hard way with the 4B model:

- three minutes of silence, and the next request starts a new conversation.
- at most MAX_MESSAGES messages; the oldest fall off, always so that the
  history begins with a user message and never between a tool call and its
  result.
- every request sets a mark; when it fails, everything since the mark is
  rolled back, so an error leaves nothing behind.
- refusals are shown but kept out of the history: the model copies what it
  sees itself say, and one refusal in the history made it refuse everything
  after it. prompt wording alone did not stop that.
- a CONFIRM proposal stays pending until the user decides; a new request or
  leaving the page counts as a rejection.
"""

import re
import time

from .chat import ToolCall

SESSION_KEY = 'assistant'
MAX_MESSAGES = 24
IDLE_SECONDS = 180

REJECTED = "abgelehnt: der Nutzer hat die Ausführung nicht bestätigt, es ist nichts passiert"
DONE = "ausgeführt"

REFUSAL = re.compile(
    r"kann ich (leider )?nicht|nicht (tun|machen|ausführen|möglich)|kein\w*( \w+)? werkzeug"
    r"|(weiß|weiss) (dazu|darüber|davon) nichts|dazu (ist )?nichts (bekannt|gefunden)"
    r"|datenrettungssonde",
    re.IGNORECASE)


def is_refusal(text):
    return bool(REFUSAL.search(text or ''))


def trim(messages):
    """drop the oldest messages until the limit holds and a user message leads."""
    while len(messages) > MAX_MESSAGES or (messages and messages[0].get('role') != 'user'):
        messages.pop(0)
    return messages


class Conversation:
    """
    the history for one browser session. load with Conversation(request.session),
    call begin() for a request, add messages, then save(); on a failure rollback()
    instead. the session only ever holds plain json: a list of chat messages, the
    time of the last request, and the pending proposal, if any.
    """

    def __init__(self, session, now=None):
        self.session = session
        self.now = now or time.time
        data = session.get(SESSION_KEY) or {}
        self.messages = list(data.get('messages') or [])
        self.pending = data.get('pending')
        self.last = data.get('last') or 0
        if self.now() - self.last > IDLE_SECONDS:
            self.reset()
        self._mark = len(self.messages)

    def reset(self):
        self.messages = []
        self.pending = None

    # one request -------------------------------------------------------------------

    def begin(self):
        """
        start a request: an open proposal is thereby rejected, then the mark is
        set so that a failure can roll back to exactly here.
        """
        if self.pending:
            self.resolve_pending(False)
        self.last = self.now()
        self._mark = len(self.messages)

    def touch(self):
        """count a confirmation as activity without starting a request."""
        self.last = self.now()

    def rollback(self):
        del self.messages[self._mark:]
        self.pending = None

    def save(self):
        trim(self.messages)
        self.session[SESSION_KEY] = {'messages': self.messages, 'pending': self.pending, 'last': self.last}
        try:
            self.session.modified = True
        except AttributeError:
            pass

    # messages ----------------------------------------------------------------------

    def add_user(self, text):
        self.messages.append({'role': 'user', 'content': text})

    def add_call(self, call: ToolCall):
        self.messages.append(call.message())

    def add_result(self, call_id, content):
        self.messages.append({'role': 'tool', 'tool_call_id': call_id, 'content': content})

    def add_answer(self, text):
        """record the model's answer; a refusal is not kept. returns whether it was."""
        if is_refusal(text):
            return False
        self.messages.append({'role': 'assistant', 'content': text})
        return True

    # confirm proposals -------------------------------------------------------------

    def set_pending(self, call: ToolCall, description):
        """the proposal is recorded as a call without result until the user decides."""
        self.add_call(call)
        self.pending = {'id': call.id, 'name': call.name, 'arguments': call.arguments, 'description': description}

    def pending_call(self):
        if not self.pending:
            return None
        return ToolCall(self.pending['name'], self.pending['arguments'], self.pending['id'])

    def resolve_pending(self, accepted):
        """close the open proposal with its result; returns the proposal, or None."""
        pending, self.pending = self.pending, None
        if pending:
            self.add_result(pending['id'], DONE if accepted else REJECTED)
        return pending
