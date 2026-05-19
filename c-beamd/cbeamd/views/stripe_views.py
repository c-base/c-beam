# -*- coding: utf-8 -*-
"""
LED Stripe and lighting control views.
"""

from django.contrib.auth.decorators import login_required
from django.http import HttpResponse
from django.shortcuts import render
from django.views.decorators.csrf import csrf_exempt

from ..forms import StripeForm
from ..json_rpc_client import jsonrpc_method
from .view_helpers import (
    cerebrum, default_stripe_offset, default_stripe_pattern, default_stripe_speed,
    models, publish
)


@jsonrpc_method('set_stripe_pattern')
def set_stripe_pattern(request, pattern_id):
    """
    set the airlock led stripe pattern
    """
    pattern_id = int(pattern_id)
    return "aye"


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
    return cerebrum.set_buffer(buffer)


@jsonrpc_method('set_stripe_default')
def set_stripe_default(request):
    """
    set the airlock led stripe pattern to the default pattern
    """
    global default_stripe_pattern, default_stripe_speed, default_stripe_offset

    if len(models.User.objects.filter(status="online")) > 0:
        default_stripe_pattern = 1
        default_stripe_speed = 3
    else:
        default_stripe_pattern = 10
        default_stripe_speed = 1
    cerebrum.set_pattern(default_stripe_pattern)
    cerebrum.set_speed(default_stripe_speed)
    return "aye"


@jsonrpc_method('notbeleuchtung')
def notbeleuchtung(request):
    """
    set the airlock led stripe pattern to emergency lights
    """
    global default_stripe_pattern, default_stripe_speed
    default_stripe_pattern = 10
    default_stripe_speed = 0
    cerebrum.set_pattern(10)
    cerebrum.set_speed(1)


@jsonrpc_method('rainbow')
def rainbow(request):
    """
    set the airlock led stripe pattern to rainbow
    """
    global default_stripe_pattern, default_stripe_speed
    default_stripe_pattern = 1
    default_stripe_speed = 3
    cerebrum.set_pattern(default_stripe_pattern)
    cerebrum.set_speed(default_stripe_speed)


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
