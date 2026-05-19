# -*- coding: utf-8 -*-
"""
Authentication views - Login and Logout functionality.
"""

import json
from datetime import timedelta

from django.contrib.auth.decorators import login_required
from django.shortcuts import render
from django.utils import timezone

from ..json_rpc_client import jsonrpc_method
from .view_helpers import (
    getuser, hysterese, log_stats, newarrivallist, publish, reply
)
from .audio_views import tts
from .user_views import getnickspell, is_logged_in


@jsonrpc_method('login_with_id')
def login_with_id(request, user):
    return "not implemented yet"


@jsonrpc_method('login')
def login(request, user):
    """
    login in to c-beam
    """
    u = getuser(user)
    if u.logouttime + timedelta(seconds=hysterese) > timezone.now():
        return reply(request, "hysterese")
    return force_login(request, user)


@jsonrpc_method('force_login')
def force_login(request, user):
    """
    login to c-beam ignoring the current status
    """
    from .user_views import who_result
    from .view_helpers import logger
    u = getuser(user)
    try:
        # monitord.login(u.username)
        pass
    except Exception:
        pass
    payload = {'user': str(u.username), 'timestamp': timezone.localtime(timezone.now()).strftime("%H:%M")}
    publish("user/entering", json.dumps(payload))
    publish('user/who', json.dumps(who_result()), retain=True)
    u.status = "online"
    u.logintime = timezone.now()
    u.save()
    log_stats()
    # logactivity(request, user, "login")
    newarrivallist[u.username] = timezone.now()
    return reply(request, "%s logged in" % u.username)


@jsonrpc_method('stealth_login')
def stealth_login(request, user):
    """
    login to c-beam without text-to-speech greeting
    """
    u = getuser(user)
    if u.logouttime + timedelta(seconds=hysterese) > timezone.now():
        return reply(request, "hysterese")
    else:
        u.status = "online"
        u.logintime = timezone.now()
        u.save()
        log_stats()
        newarrivallist[u.username] = timezone.now()
    return reply(request, "%s logged in" % u.username)


@login_required
def login_web(request):
    result = force_login(request, request.user.username)
    return render(request, 'cbeamd/c_buttons.django', {'result': 'du wurdest angemeldet'})


@jsonrpc_method('logout')
def logout(request, user):
    """
    log out from c-beam
    """
    u = getuser(user)
    if u.logintime + timedelta(seconds=hysterese) > timezone.now():
        return reply(request, "hysterese")
    return force_logout(request, user)


@jsonrpc_method('stealth_logout')
def stealth_logout(request, user):
    """
    log out from c-beam without text-to-speech greeting
    """
    u = getuser(user)
    if u.logintime + timedelta(seconds=hysterese) > timezone.now():
        return reply(request, "hysterese")
    else:
        u.status = "offline"
        u.logouttime = timezone.now()
        u.save()
    return reply(request, "%s logged out" % u.username)


@jsonrpc_method('force_logout')
def force_logout(request, user):
    """
    log out from c-beam ignoring the current status
    """
    from .user_views import who_result
    u = getuser(user)
    try:
        # monitord.logout(u.username)
        pass
    except Exception:
        pass
    payload = {'user': str(u.username), 'timestamp': timezone.localtime(timezone.now()).strftime("%H:%M")}
    publish("user/leaving", json.dumps(payload))
    publish('user/who', json.dumps(who_result()), retain=True)
    oldstatus = u.status
    u.status = "offline"
    u.logouttime = timezone.now()
    u.save()
    log_stats()
    if u.logintime + timedelta(minutes=60) < timezone.now() and oldstatus == "online":
        from .activity_views import logactivity
        logactivity(request, user, "logout", 2)
    return reply(request, "%s logged out" % u.username)


@login_required
def logout_web(request):
    result = force_logout(request, request.user.username)
    return render(request, 'cbeamd/c_buttons.django', {'result': 'du wurdest abgemeldet'})


# jsonrpc_method('login_wlan')
@jsonrpc_method('wifi_login')
def login_wlan(request, user):
    """
    login to c-beam via wifi
    """
    from .view_helpers import logger
    u = getuser(user)
    if u.stealthmode > timezone.now():
        return "user in stealth mode"
    if is_logged_in(u.username):
        logger.debug('extend user: %s' % user)
        extend(user)
    else:
        logger.debug('login user: %s' % user)
        if u.logouttime + timedelta(minutes=30) < timezone.now():
            login(request, user)
        else:
            pass


def extend(user):
    u = getuser(user)
    u.status = "online"
    u.extendtime = timezone.now()
    u.save()
    return "aye"


@jsonrpc_method('tagevent')
def tagevent(request, user):
    if is_logged_in(user):  # TODO and logintimeout
        return logout(request, user)
    else:
        return login(request, user)


@jsonrpc_method('unknown_tag')
def unknown_tag(request, rfid):
    from .view_helpers import models
    from .audio_views import monmessage
    u = models.User.objects.filter(rfid__icontains=rfid)
    if len(u) > 0:
        return tagevent(request, u[0].username)
    else:
        return monmessage(request, rfid)


def welcometts(request, user):
    # if os.path.isfile('%s/%s/hello.mp3' % (cfg.sampledir, user)):
    #    os.system('mpg123 %s/%s/hello.mp3' % (cfg.sampledir, user))
    # else:
    if getnickspell(request, user) != "NONE":
        if user == "kristall":
            tts(request, "Julia", "a loa crew")
        else:
            from .view_helpers import cfg
            tts(request, "Julia", cfg.ttsgreeting % getnickspell(request, user))
