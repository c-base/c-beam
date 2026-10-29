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

import cbeamdcfg as cfg

from ..assistant import chat, engine
from ..assistant.chat import AssistantError

# 20 s at 16 kHz mono 16 bit are 640 kB; anything far beyond that is not a recording
MAX_UPLOAD = 2 * 1024 * 1024


def assistant_context(request):
    """what assistant_terminal.django needs, for every page that embeds it."""
    configured = chat.configured()
    return {
        'assistant_configured': configured,
        'assistant_models': chat.models() if configured else [],
        'assistant_model': request.session.get(engine.MODEL_KEY) or '',
        'assistant_default_model': cfg.ai_model,
    }


@login_required
def assistant_page(request):
    context = assistant_context(request)
    context['assistant_prompt_line'] = 'hallo %s. frag mich etwas, oder sag mir, was ich tun soll.' % request.user.username
    return render(request, 'cbeamd/assistant.django', context)


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


@require_POST
def assistant_transcribe(request):
    """multipart field "file" (wav) → {"text": "…"} or {"error": "…"}."""
    if not request.user.is_authenticated:
        return JsonResponse({'text': None, 'error': 'nicht eingeloggt'}, status=403)
    upload = request.FILES.get('file')
    if upload is None:
        return JsonResponse({'text': None, 'error': 'keine aufnahme'}, status=400)
    if upload.size > MAX_UPLOAD:
        return JsonResponse({'text': None, 'error': 'aufnahme zu groß'}, status=400)
    try:
        text = chat.transcribe(upload.read(), upload.name or 'speech.wav')
    except AssistantError as e:
        return JsonResponse({'text': None, 'error': str(e)})
    return JsonResponse({'text': text, 'error': None})


@require_POST
@_guarded
def assistant_model(request, body):
    """{"model": "…"} picks the chat model for this session; "" goes back to the default."""
    model = body.get('model')
    if not isinstance(model, str):
        return _reply(engine.Reply.error("ungu:ltige anfrage"), status=400)
    model = model.strip()
    if model and model not in {m['id'] for m in chat.models()}:
        return _reply(engine.Reply.error("unbekanntes modell"), status=400)
    request.session[engine.MODEL_KEY] = model
    return _reply(engine.Reply().add('info', 'modell: ' + (model or cfg.ai_model + ' (standard)')))
