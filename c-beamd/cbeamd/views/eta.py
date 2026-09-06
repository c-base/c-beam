"""
ETA / arrival tracking.

Split out of the original views.py; function bodies are unchanged.
"""

import json
import re
from datetime import datetime, timedelta

from django.utils import timezone
from ..json_rpc_client import jsonrpc_method

from ..models import Mission, User
from ..tools.LEDStripe import *

from . import helpers
from .helpers import eta_timeout
from .audio import tts
from .helpers import getuser, getuser_eta, log_stats, publish, userlist
from .missions import gcm_send
from .stripe import set_stripe_default
from .user import getnickspell, who_result


@jsonrpc_method('available')
def available(request):
    cleanup(request)
    return userlist()


def etalist():
    result = {}
    for u in User.objects.filter(status="eta").order_by('username'):
        result[u.username] = u.eta
    return result


@jsonrpc_method('who')
def who(request):
    """list all user that have logged in."""
    cleanup(request)
    return who_result()


#################################################################
# ETA
#################################################################

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

    # if the first argument is a weekday, delegate to LTE
    # TODO
    # if text[:2].upper() in weekdays:
        # return lte(bot, ievent)

    if text in ('gleich', 'bald', 'demnaechst', 'demnächst', 'demn\xe4chst'):
        etaval = datetime.now() + timedelta(minutes=30)
        eta = etaval.strftime("%H%M")
    elif text.startswith('+'):
        foo = int(text[1:])
        etaval = datetime.now() + timedelta(minutes=foo)
        eta = etaval.strftime("%H%M")
    # elif ievent.rest == 'heute nicht mehr':
    #    eta = "0"
    else:
        eta = text
    # remove superflous colons
    eta = re.sub(r'(\d\d):(\d\d)', r'\1\2', eta)
    # eta = re.sub(r'(\d\d).(\d\d)',r'\1\2',eta)

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
    # data['newetas'][user] = eta

    u = getuser_eta(user)
    if u is None:
        return "you do not exist"

    helpers.newetalist[user] = eta
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
                gcm_send(request, 'ETA', '%s (%s)' % (user, eta))
            except Exception:
                pass
        payload = {'user': str(u.username), 'timestamp': timezone.localtime(timezone.now()).strftime("%H:%M"), 'eta': eta}
        publish("user/eta", json.dumps(payload))
        # publish("user/eta", '%s (%s)' % (user, eta))
        log_stats()
        return 'eta_set'


def extract_eta(text):
    m = re.match(r'^.*?(\d\d\d\d).*', text)
    if m:
        return m.group(1)
    else:
        return "9999"


@jsonrpc_method('subeta')
def subeta(request, user):
    """
    subscripe to ETA notifications via XMPP/IRC
    """
    u = getuser(user)
    u.etasub = True
    u.save()


@jsonrpc_method('unsubeta')
def unsubeta(request, user):
    """
    unsubscripe to ETA notifications via XMPP/IRC
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
    tmp = helpers.newetalist
    helpers.newetalist = {}
    return tmp


@jsonrpc_method('arrivals')
def arrivals(request):
    tmp = helpers.newarrivallist
    helpers.newarrivallist = {}
    return tmp


@jsonrpc_method('achievements')
def achievements(request):
    tmp = helpers.achievements
    helpers.achievements = {}
    return tmp


@jsonrpc_method('activities')
def activities(request):
    tmp = helpers.newactivities
    helpers.newactivities = []
    return tmp


@jsonrpc_method('cleanup')
def cleanup(request):
    users = userlist()
    usercount = len(users)
    autologout = False

    now = int(timezone.now().strftime("%Y%m%d%H%M%S"))

    # remove expired users
    for u in User.objects.filter(status="online"):
        if u.autologout_in() <= 0:
            autologout = True
            u.status = "offline"
            u.logouttime = timezone.now()
            u.save()
            log_stats()

    # remove expired ETAs
    for u in User.objects.filter(status="eta"):
        if u.etatimestamp < timezone.now():
            u.eta = ""
            u.status = "offline"
            u.save()
            log_stats()

    # remove expired ETDs

    if autologout:
        try:
            set_stripe_default(request)
        except Exception:
            pass

    for mission in Mission.objects.filter(status="completed").filter(repeat_after_days__gte=0):
        if mission.completed_on + timedelta(mission.repeat_after_days) > timezone.now():
            mission.status = "open"
            mission.save()

    publish('user/who', json.dumps(who_result()), retain=True)
    return "aye"
