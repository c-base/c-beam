# -*- coding: utf-8 -*-
"""
User preference views - stats, push notifications, stealth mode.
"""

import json
from datetime import timedelta

from django.contrib.auth.decorators import login_required
from django.http import HttpResponse
from django.shortcuts import render
from django.utils import timezone

from ..json_rpc_client import jsonrpc_method
from .helpers import c_out_volume, getuser, models, send_mail, create_random_password


reminder_store = {}


def reminder():
    return reminder_store


@jsonrpc_method('set_stats_enabled')
def set_stats_enabled(request, user, is_enabled):
    """
    enable or disable stats tracking for user
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
    volume = c_out_volume
    return render(request, 'cbeamd/c_out_volume.django', locals())


@login_required
def c_out_volume_json(request):
    return HttpResponse(json.dumps({'volume': c_out_volume}), content_type="application/json")


def c_out_volume_set(request, volume):
    global c_out_volume
    c_out_volume = volume
    return HttpResponse(json.dumps({'result': "OK"}), content_type="application/json")


@jsonrpc_method('set_first_password')
def set_first_password(request, user):
    u = getuser(user)
    recipient = '%s@c-base.org' % u.username
    token = 'generierteseinmaltoken'
    text = 'hallo %s\n\n' % u.username
    text += '$jemand, wahrscheinlich du selbst, hat dein c-beam initialpasswort gesetzt.\n\nklicke auf den folgenden link, '
    text += 'um das passwort zu aktivieren:\n\n'
    text += 'https://ein-link-der-von-ueberall-erreichbar-sein-sollte.org/approve/%s\n\n' % token
    text += 'du solltest dein initialpasswort mo:glchst bald unter https://member.cbrp3.c-base.org und in der app a:ndern.\n\n'
    text += 'dance fu:r die beachtung der sicherheitshinweise\nihr bordcomputer\n\n'
    send_mail(recipient, text)


@jsonrpc_method('set_stealthmode')
def set_stealthmode(request, user, duration):
    """
    enable stealthmode for user for duration in hours
    """
    u = getuser(user)
    u.stealthmode = timezone.now() + timedelta(hours=duration)
    u.save()
    return "aye"


@jsonrpc_method('get_stealthmode')
def get_stealthmode(request, user):
    u = getuser(user)
    return str(u.stealthmode)


@jsonrpc_method('set_wlan_login')
def set_wlan_login(request, user, enabled):
    u = getuser(user)
    u.wlanlogin = enabled
    u.save()
    return "aye"


@jsonrpc_method('isWifiLoginEnabled()')
def isWifiLoginEnabled(request, users):
    return {user.username: user.wlanlogin for user in models.User.objects.filter(username__in=users)}
