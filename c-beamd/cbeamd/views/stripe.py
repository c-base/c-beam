"""
LED stripe control in the airlock (c_leuse).

the leds moved from the cerebrum json-rpc service to an arduino behind
c_leuse_leds.py (github.com/c-base/c_leuse), which subscribes to the c-base
mqtt broker and hands the payload of `c_leuse/led_pattern` straight to the
firmware's setPattern(char*). the firmware knows these names:

    off, notbeleuchtung, scanning, success, failure

and shows rainbow for anything else. there is no speed, offset or buffer any
more; the json-rpc methods for those are kept so old clients get an answer
instead of a "method not found", but they do nothing.
"""

from django.shortcuts import render
from django.views.decorators.csrf import csrf_exempt
from ..json_rpc_client import jsonrpc_method

import cbeamdcfg as cfg
from ..forms import StripeForm
from ..models import User

from . import helpers
from .helpers import logger, publish

# names the firmware understands. anything else falls through to rainbow on
# the arduino, so rainbow is listed here only for the ui and the mapping below.
PATTERNS = ('rainbow', 'off', 'notbeleuchtung', 'scanning', 'success', 'failure')

# the numeric pattern ids of the old cerebrum api, as used by the android app
# and the old web ui. colours have no counterpart on the new stripe; green and
# red are mapped to the closest thing it has, everything else becomes rainbow.
LEGACY_PATTERNS = {
    0: 'off',
    1: 'rainbow',
    2: 'success',        # grün
    4: 'failure',        # rot
    6: 'rainbow',        # "default"
    10: 'notbeleuchtung',
}

# legacy ids, kept for helpers.default_stripe_pattern which other modules read
LEGACY_RAINBOW = 1
LEGACY_NOTBELEUCHTUNG = 10

NOT_SUPPORTED = "not supported by the c_leuse leds, pattern only"


def pattern_name(pattern):
    """
    normalise a pattern given as name or legacy numeric id to a firmware name.
    """
    if isinstance(pattern, str) and not pattern.lstrip('-').isdigit():
        name = pattern.strip().lower()
        if name not in PATTERNS:
            logger.warning("unknown led pattern %r, the stripe will show rainbow", pattern)
        return name
    pattern_id = int(pattern)
    name = LEGACY_PATTERNS.get(pattern_id)
    if name is None:
        logger.warning("legacy led pattern id %d has no equivalent, using rainbow", pattern_id)
        name = 'rainbow'
    return name


def send_pattern(pattern):
    """
    publish a pattern to the airlock stripe. retained, so c_leuse_leds picks
    the current pattern up again when it reconnects or restarts.
    """
    name = pattern_name(pattern)
    publish(cfg.c_leuse_led_topic, name, retain=True)
    return name


#################################################################
# c_leuse led methods
#################################################################

@jsonrpc_method('set_stripe_pattern')
def set_stripe_pattern(request, pattern_id):
    """
    set the airlock led stripe pattern. takes a pattern name (off, rainbow,
    notbeleuchtung, scanning, success, failure) or one of the old numeric ids.
    """
    return send_pattern(pattern_id)


def set_stripe_pattern_web(request, pattern_id):
    name = send_pattern(pattern_id)
    return render(request, 'cbeamd/c_leuse.django', {'result': 'Pattern %s wurde gesetzt' % name})


@jsonrpc_method('set_stripe_speed')
def set_stripe_speed(request, speed):
    """
    no-op: the c_leuse leds have no speed setting
    """
    logger.info("set_stripe_speed(%s) ignored: %s", speed, NOT_SUPPORTED)
    return NOT_SUPPORTED


def set_stripe_speed_web(request, speed):
    return render(request, 'cbeamd/c_leuse.django', {'result': 'Geschwindigkeit wird von den neuen LEDs nicht unterstuetzt'})


@jsonrpc_method('set_stripe_offset')
def set_stripe_offset(request, offset):
    """
    no-op: the c_leuse leds have no offset setting
    """
    logger.info("set_stripe_offset(%s) ignored: %s", offset, NOT_SUPPORTED)
    return NOT_SUPPORTED


@jsonrpc_method('set_stripe_buffer')
def set_stripe_buffer(request, buffer):
    """
    no-op: the c_leuse leds cannot take a raw buffer
    """
    logger.info("set_stripe_buffer ignored: %s", NOT_SUPPORTED)
    return NOT_SUPPORTED


@jsonrpc_method('set_stripe_default')
def set_stripe_default(request):
    """
    set the airlock led stripe to the default pattern: rainbow while someone
    is on board, notbeleuchtung when the station is empty
    """
    if User.objects.filter(status="online").exists():
        helpers.default_stripe_pattern = LEGACY_RAINBOW
        helpers.default_stripe_speed = 3
    else:
        helpers.default_stripe_pattern = LEGACY_NOTBELEUCHTUNG
        helpers.default_stripe_speed = 1
    send_pattern(helpers.default_stripe_pattern)
    return "aye"


@jsonrpc_method('notbeleuchtung')
def notbeleuchtung(request):
    """
    set the airlock led stripe pattern to emergency lights
    """
    helpers.default_stripe_pattern = LEGACY_NOTBELEUCHTUNG
    helpers.default_stripe_speed = 0
    return send_pattern('notbeleuchtung')


@jsonrpc_method('rainbow')
def rainbow(request):
    """
    set the airlock led stripe pattern to rainbow
    """
    helpers.default_stripe_pattern = LEGACY_RAINBOW
    helpers.default_stripe_speed = 3
    return send_pattern('rainbow')


@csrf_exempt
def stripe_view(request):
    if request.method == 'POST':
        form = StripeForm(request.POST)
        if form.is_valid():
            form.cleaned_data["speed"]
            form.cleaned_data["pattern"]
            form.cleaned_data["offset"]
            return render(request, 'cbeamd/stripe_form.django', {'form': form})
    else:
        form = StripeForm()
        return render(request, 'cbeamd/stripe_form.django', {'form': form})
