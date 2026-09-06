"""
User preference toggles.

Split out of the original views.py; function bodies are unchanged.
"""

import json
from datetime import timedelta

from django.contrib.auth.decorators import login_required
from django.http import HttpResponse
from django.shortcuts import render
from django.utils import timezone
from ..json_rpc_client import jsonrpc_method

from ..models import User

from . import helpers
from .helpers import getuser


@jsonrpc_method('isWifiLoginEnabled()')
def isWifiLoginEnabled(request, users):
    return {user.username: user.wlanlogin for user in User.objects.filter(username__in=users)}


@jsonrpc_method('set_wlan_login')
def set_wlan_login(request, user, enabled):
    u = getuser(user)
    u.wlanlogin = enabled
    u.save()
    return "aye"


@jsonrpc_method('set_stats_enabled')
def set_stats_enabled(request, user, is_enabled):
    """
    enable or disable c-game stats
    """
    u = getuser(user)
    if type(is_enabled) is bool:
        u.stats_enabled = is_enabled
    else:
        if is_enabled == "true":
            u.stats_enabled = True
        else:
            u.stats_enabled = False
    u.save()
    return "aye"


@jsonrpc_method('set_push_missions')
def set_push_missions(request, user, is_enabled):
    """
    enable or disable push notifications for completed missions
    """
    u = getuser(user)
    if type(is_enabled) is bool:
        u.push_missions = is_enabled
    else:
        if is_enabled == "true":
            u.push_missions = True
        else:
            u.push_missions = False
    u.save()
    return "aye"


@jsonrpc_method('set_push_boarding')
def set_push_boarding(request, user, is_enabled):
    """
    enable or disable push notifications for boarding members
    """
    u = getuser(user)
    if type(is_enabled) is bool:
        u.push_boarding = is_enabled
    else:
        if is_enabled == "true":
            u.push_boarding = True
        else:
            u.push_boarding = False
    u.save()
    return "aye"


@jsonrpc_method('set_push_eta')
def set_push_eta(request, user, is_enabled):
    """
    enable or disable push notifications for ETAs
    """
    u = getuser(user)
    if type(is_enabled) is bool:
        u.push_eta = is_enabled
    else:
        if is_enabled == "true":
            u.push_eta = True
        else:
            u.push_eta = False
    u.save()
    return "aye"


@login_required
def c_out_volume_web(request):
    volume = helpers.c_out_volume
    return render(request, 'cbeamd/c_out_volume.django', locals())


@login_required
def c_out_volume_json(request):
    return HttpResponse(json.dumps({'volume': helpers.c_out_volume}), content_type="application/json")


def c_out_volume_set(request, volume):
    helpers.c_out_volume = volume
    return HttpResponse(json.dumps({'result': "OK"}), content_type="application/json")


@jsonrpc_method('set_stealthmode')
def set_stealthmode(request, user, duration):
    """
    enable stealthmode for user for duration in hours
    """
    u = getuser(user)
    u.stealthmode = timezone.now() + timedelta(hours=duration)
    u.save()
    return "aye"


# @jsonrpc_method('get_stealthmode')
def get_stealthmode(request, user):
    u = getuser(user)
    return str(u.stealthmode)
