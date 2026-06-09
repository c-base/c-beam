# -*- coding: utf-8 -*-
"""
ETA (Estimated Time of Arrival) tracking views.
"""

import json
import re
from datetime import datetime, timedelta

from django.utils import timezone

from ..json_rpc_client import jsonrpc_method
from .helpers import (
    eta_timeout, getuser, getuser_eta, log_stats, models,
    newetalist, publish, reply
)
from .audio import tts
from .user import getnickspell


@jsonrpc_method('eta')
def eta(request, user, text):
    """
    set eta for user to the time specified in text (HHMM free text)
    """
    eta = "0"
    u = getuser_eta(user)
    if u is None:
        return "meh"
    if user == 'bernd':
        return "meh"

    if text in ('gleich', 'bald', 'demnaechst', 'demnächst', 'demn\xe4chst'):
        etaval = datetime.now() + timedelta(minutes=30)
        eta = etaval.strftime("%H%M")
    elif text.startswith('+'):
        foo = int(text[1:])
        etaval = datetime.now() + timedelta(minutes=foo)
        eta = etaval.strftime("%H%M")
    else:
        eta = text
    # remove superfluous colons
    eta = re.sub(r'(\d\d):(\d\d)', r'\1\2', eta)

    if eta != "0" and extract_eta(eta) == "9999":
        return 'err_timeparser'
    etatime = extract_eta(eta)
    hour = int(etatime[0:2])
    minute = int(etatime[2:4])

    tts(request, "Julia", "E.T.A. %s: %d Uhr %d ." % (getnickspell(request, user), hour, minute))
    return seteta(request, user, eta)


@jsonrpc_method('seteta')
def seteta(request, user, eta):
    """
    set eta for user to the time specified in eta (HHMM)
    """
    u = getuser_eta(user)
    if u is None:
        return "you do not exist"

    newetalist[user] = eta
    if eta == '0':
        # delete eta for user
        u.eta = ""
        u.status = "offline"
        u.save()
        log_stats()
        return 'eta_removed'
    else:
        arrival = extract_eta(eta)

        arrival_hour = int(arrival[0:2]) % 24
        arrival_minute = int(arrival[3:4]) % 60

        etatimestamp = timezone.now().replace(hour=arrival_hour, minute=arrival_minute) + timedelta(minutes=eta_timeout)

        if timezone.now().strftime("%H%M") > arrival:
            etatimestamp = etatimestamp + timedelta(days=1)

        u.eta = eta
        u.etatimestamp = etatimestamp
        u.status = "eta"
        u.save()
        if not u.no_google:
            try:
                from .missions import gcm_send
                gcm_send(request, 'ETA', '%s (%s)' % (user, eta))
            except Exception:
                pass
        payload = {'user': str(u.username), 'timestamp': timezone.localtime(timezone.now()).strftime("%H:%M"), 'eta': eta}
        publish("user/eta", json.dumps(payload))
        log_stats()
        return 'eta_set'


def extract_eta(text):
    m = re.match(r'^.*?(\d\d\d\d).*', text)
    if m:
        return m.group(1)
    else:
        return "9999"


def etalist():
    result = {}
    for u in models.User.objects.filter(status="eta").order_by('username'):
        result[u.username] = u.eta
    return result


@jsonrpc_method('subeta')
def subeta(request, user):
    """
    subscribe to ETA notifications via XMPP/IRC
    """
    u = getuser(user)
    u.etasub = True
    u.save()


@jsonrpc_method('unsubeta')
def unsubeta(request, user):
    """
    unsubscribe to ETA notifications via XMPP/IRC
    """
    u = getuser(user)
    u.etasub = False
    u.save()


@jsonrpc_method('subarrive')
def subarrive(request, user):
    """
    subscribe to boarding notifications via XMPP/IRC
    """
    u = getuser(user)
    u.arrivesub = True
    u.save()


@jsonrpc_method('unsubarrive')
def unsubarrive(request, user):
    """
    unsubscribe to boarding notifications via XMPP/IRC
    """
    u = getuser(user)
    u.arrivesub = False
    u.save()


@jsonrpc_method('newetas')
def newetas(request):
    tmp = newetalist
    newetalist.clear()
    newetalist.update({})
    return tmp


@jsonrpc_method('arrivals')
def arrivals(request):
    from .helpers import newarrivallist
    tmp = newarrivallist
    newarrivallist.clear()
    newarrivallist.update({})
    return tmp


@jsonrpc_method('achievements')
def achievements(request):
    from .helpers import achievements as achievements_store
    tmp = achievements_store
    achievements_store.clear()
    achievements_store.update({})
    return tmp


@jsonrpc_method('activities')
def activities(request):
    from .helpers import newactivities
    tmp = newactivities
    newactivities.clear()
    return tmp


@jsonrpc_method('cleanup')
def cleanup(request):
    """
    Clean up expired users, ETAs, and missions.
    """
    from .stripe import set_stripe_default
    from .user import userlist, who_result
    from .helpers import log_stats, models, mission_completed, publish

    users = userlist()
    usercount = len(users)
    autologout = False

    # remove expired users
    for u in models.User.objects.filter(status="online"):
        if u.autologout_in() <= 0:
            autologout = True
            u.status = "offline"
            u.logouttime = timezone.now()
            u.save()
            log_stats()

    # remove expired ETAs
    for u in models.User.objects.filter(status="eta"):
        if u.etatimestamp < timezone.now():
            u.eta = ""
            u.status = "offline"
            u.save()
            log_stats()

    if autologout:
        try:
            set_stripe_default(request)
        except Exception:
            pass

    for mission in models.Mission.objects.filter(status=mission_completed).filter(repeat_after_days__gte=0):
        if mission.completed_on + timedelta(mission.repeat_after_days) > timezone.now():
            mission.status = "open"
            mission.save()

    publish('user/who', json.dumps(who_result()), retain=True)
    return "aye"


@jsonrpc_method('who')
def who(request):
    """list all user that have logged in."""
    cleanup(request)
    from .user import who_result
    return who_result()
