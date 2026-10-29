"""
the web assistant (AI-ASSISTANT.md): the page with the terminal and the two
json endpoints it talks to. everything else, the model, the tools and the
conversation, lives in cbeamd.assistant; the browser only ever talks to
c-beam.

the json endpoints answer 403 instead of redirecting when nobody is logged in,
so that the page's javascript sees a clear error rather than the login page.
"""

import json

from django.contrib.auth.decorators import login_required
from django.http import JsonResponse
from django.shortcuts import render
from django.views.decorators.http import require_POST

from ..assistant import chat, engine


@login_required
def assistant_page(request):
    return render(request, 'cbeamd/assistant.django', {
        'configured': chat.configured(),
        'username': request.user.username,
    })


def _json_body(request):
    try:
        body = json.loads(request.body.decode('utf-8') or '{}')
    except (ValueError, UnicodeDecodeError):
        return None
    return body if isinstance(body, dict) else None


def _reply(reply, status=200):
    return JsonResponse({'lines': reply.lines, 'speak': reply.speak, 'confirm': reply.confirm}, status=status)


def _guarded(view):
    """login as 403 json, a bad body as 400 json."""
    def wrapper(request):
        if not request.user.is_authenticated:
            return _reply(engine.Reply.error("nicht eingeloggt"), status=403)
        body = _json_body(request)
        if body is None:
            return _reply(engine.Reply.error("ungu:ltige anfrage"), status=400)
        return view(request, body)
    wrapper.__name__ = view.__name__
    wrapper.__doc__ = view.__doc__
    return wrapper


@require_POST
@_guarded
def assistant_ask(request, body):
    """{"text": "…", "voice": false} → the terminal lines for the answer."""
    text = body.get('text')
    if not isinstance(text, str):
        return _reply(engine.Reply.error("ungu:ltige anfrage"), status=400)
    return _reply(engine.ask(request, text, voice=bool(body.get('voice'))))


@require_POST
@_guarded
def assistant_confirm(request, body):
    """{"id": "call_…", "accept": true} → run or drop the open proposal."""
    call_id = body.get('id')
    if not isinstance(call_id, str):
        return _reply(engine.Reply.error("ungu:ltige anfrage"), status=400)
    return _reply(engine.confirm(request, call_id, bool(body.get('accept'))))
