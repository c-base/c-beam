"""
the template context of the assistant's terminal (assistant_terminal.django),
as a context processor: every page of a logged-in crew member gets the
terminal below its content (base.django), / and /assistant embed it
themselves. the model list is cached in chat.models(), so this costs nothing
per page once the server has been asked.
"""

import cbeamdcfg as cfg

from . import chat
from .engine import MODEL_KEY

PROMPT_LINE = 'frag mich etwas, oder sag mir, was ich tun soll.'


def assistant(request):
    user = getattr(request, 'user', None)
    if user is None or not user.is_authenticated:
        return {'assistant_available': False, 'assistant_configured': False}
    configured = chat.configured()
    return {
        # the terminal on an ordinary page: only with a server and a login
        'assistant_available': configured,
        'assistant_configured': configured,
        'assistant_models': chat.models() if configured else [],
        'assistant_model': request.session.get(MODEL_KEY) or '',
        'assistant_default_model': cfg.ai_model,
        'assistant_prompt_line': PROMPT_LINE,
    }
