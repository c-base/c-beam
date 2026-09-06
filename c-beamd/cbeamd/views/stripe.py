"""
LED stripe control.

Split out of the original views.py; function bodies are unchanged.
"""

import random

from django.shortcuts import render
from django.views.decorators.csrf import csrf_exempt
from ..json_rpc_client import jsonrpc_method

from ..forms import StripeForm
from ..models import User
from ..tools.LEDStripe import *

from . import helpers
from .helpers import cerebrum

#################################################################
# cerebrum leds methods
#################################################################

@jsonrpc_method('set_stripe_pattern')
def set_stripe_pattern(request, pattern_id):
    """
    set the airlock led stripe pattern to pattern_id
    """
    pattern_id = int(pattern_id)
    # if pattern_id == 0:
    # return cerebrum.partymode()
    # if pattern_id == 4:
    # return cerebrum.flimmer()
    if pattern_id == 7:
        return cerebrum.statics()
    if pattern_id == 3:
        patterns = cerebrum.get_patterns()
        return cerebrum.set_pattern(random.choice(patterns))
    # if pattern_id < 20:
    result = cerebrum.set_pattern(pattern_id)
    # if pattern_id == 20:
    # result = cerebrum.flimmer()
    # if pattern_id == 21:
    # result = cerebrum.senso()
    # if pattern_id == 22:
    # result = cerebrum.blink()
    # if pattern_id == 23:
    # result = cerebrum.partymode()
    # if result['result'] == "aye":
    # result['result'] = "pattern has been set"
    # else:
    # result['result'] = "failed to set pattern"
    return result


def set_stripe_pattern_web(request, pattern_id):
    return render(request, 'cbeamd/c_leuse.django', {'result': 'Pattern wurde gesetzt'})


@jsonrpc_method('set_stripe_speed')
def set_stripe_speed(request, speed):
    """
    set the airlock led stripe speed
    """
    speed = int(speed)
    return cerebrum.set_speed(speed)


def set_stripe_speed_web(request, speed):
    cerebrum.set_speed(int(speed))
    return render(request, 'cbeamd/c_leuse.django', {'result': 'Geschwindigkeit wurde gesetzt'})


@jsonrpc_method('set_stripe_offset')
def set_stripe_offset(request, offset):
    """
    set the airlock led stripe pattern offset
    """
    offset = int(offset)
    return cerebrum.set_offset(offset)


@jsonrpc_method('set_stripe_buffer')
def set_stripe_buffer(request, buffer):
    """
    set the airlock led stripe pattern buffer
    """
    # buffer = [255,0,0,255,0,0,255,0,0,255,0,0,0,255,0,0,255,0,0,255,0,0,255,0,0,0,255,0,0,255,0,0,255,0,0,255,0,0,0,0,0,0,0,0,0,0,0,0]*32+[0,0,0,0,0,0,0,0,0,0,0,0]
    return cerebrum.set_buffer(buffer)


@jsonrpc_method('set_stripe_default')
def set_stripe_default(request):
    """
    set the airlock led stripe pattern to the default pattern
    """

    if len(User.objects.filter(status="online")) > 0:
        helpers.default_stripe_pattern = 1
        helpers.default_stripe_speed = 3
    else:
        helpers.default_stripe_pattern = 10
        helpers.default_stripe_speed = 1
    cerebrum.set_pattern(helpers.default_stripe_pattern)
    cerebrum.set_speed(helpers.default_stripe_speed)
    # cerebrum.set_offset(default_stripe_offset)
    return "aye"


@jsonrpc_method('notbeleuchtung')
def notbeleuchtung(request):
    """
    set the airlock led stripe pattern to emergency lights
    """
    helpers.default_stripe_pattern = 10
    helpers.default_stripe_speed = 0
    cerebrum.set_pattern(10)
    cerebrum.set_speed(1)
    # TODO: send MQTT message for new c-leuse LEDs


@jsonrpc_method('rainbow')
def rainbow(request):
    """
    set the airlock led stripe pattern to rainbow
    """
    helpers.default_stripe_pattern = 1
    helpers.default_stripe_speed = 3
    cerebrum.set_pattern(helpers.default_stripe_pattern)
    cerebrum.set_speed(helpers.default_stripe_speed)


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
