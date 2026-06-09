# -*- coding: utf-8 -*-
"""
Display views - weather, sensors, nerdctrl, dashboards.
"""

import json
import os
import requests
from datetime import date

from django.contrib.auth.decorators import login_required
from django.http import HttpResponse
from django.shortcuts import render

from .. import models
from ..json_rpc_client import jsonrpc_method
from .helpers import (
    c_out_volume, cerebrum_state, hand, hwstorage_state, publish
)
from ..tools.ddate import DDate


def toggle_burningman(request):
    return render(request, 'cbeamd/burningman.django', {})


def nerdctrl(request):
    return render(request, 'cbeamd/nerdctrl.django', {})


def cbeamviewer(request):
    return render(request, 'cbeamd/cbeamviewer.django', {})


def weather(request):
    return render(request, 'cbeamd/weather.django', {})


def bvg(request):
    return render(request, 'cbeamd/bvg.django', {})


def welcome(request, user):
    from .auth import welcometts
    welcometts(request, user)
    return render(request, 'cbeamd/welcome.django', {'user': user})


def sensors(request):
    return render(request, 'cbeamd/sensors.django', {})


def fakelevels(request):
    levels = []
    for i in range(1, 8):
        levels.append({'level': i, 'value': 0})
    return HttpResponse(json.dumps(levels), content_type="application/json")


def dash(request):
    return render(request, 'cbeamd/dash.django', {
        'hwstorage_state': hwstorage_state,
    })


def mechdisplay(request):
    return render(request, 'cbeamd/mechdisplay.django', {})


def he1display(request):
    return render(request, 'cbeamd/he1display.django', {})


def ceitlochclocc(request):
    from .user import ceitloch
    return render(request, 'cbeamd/ceitlochclocc.django', {'ceitloch': ceitloch()})


def donut(request):
    return render(request, 'cbeamd/donut.django', {})


def reddit(request):
    import feedparser
    d = feedparser.parse('https://www.reddit.com/r/c-base/.rss')
    return render(request, 'cbeamd/reddit.django', {'entries': d['entries']})


def barbutton(request):
    return render(request, 'cbeamd/barbutton.django', {})


@jsonrpc_method('setdigitalmeter')
def setdigitalmeter(request, meterid, value):
    os.system('curl -d \'{"method":"set_digital_meter","id":0,"params":[%d,"%s"]}\' http://altar.cbrp3.c-base.org:4568/jsonrpc' % (meterid, value))
    return "aye"


@jsonrpc_method('ddate')
def ddate(request):
    """
    returns the current ddate
    """
    now = DDate()
    now.fromDate(date.today())
    return "Today is " + str(now)


@jsonrpc_method('fnord')
def fnord(request):
    return DDate().fnord()


@jsonrpc_method('lte')
def lte(request, user, text):
    from .user import getuser
    from .helpers import logger
    u = getuser(user)
    logger.debug("lte: %s %s" % (user, text))
    import feedparser
    d = feedparser.parse('https://www.c-base.org/calendar/exported/c-base-events.ics')
    for event in d.entries:
        if text.lower() in event.summary.lower():
            return event.summary
    return "keine events gefunden"


@login_required
def ampel(request, location, color, state):
    payload = '{"%s": %d}' % (color, int(state))
    publish("ampel/%s" % location, str(payload))


@jsonrpc_method('ampelblink')
def ampelblink(request, location, color, state):
    payload = '{"%s": %d}' % (color, int(state))
    publish("ampel/%s/blink" % location, str(payload))


def issues(request):
    url = "https://api.github.com/repos/c-base/c-beam/issues"
    response = requests.get(url=url, params=dict(state='open'))
    issues = response.json()
    return issues


@jsonrpc_method('hand_help')
def hand_help(request):
    return hand.getHandHelp()


@jsonrpc_method('hand_commands')
def hand_commands(request):
    return hand.getHandCommands()


@jsonrpc_method('hand_translate')
def hand_translate(request, command):
    return hand.translate(command)


@jsonrpc_method("cerebrumNotify")
def cerebrumNotify(request, device_name, event_source_path, new_state):
    cerebrum_state[device_name][event_source_path] = new_state

    from .helpers import logger
    logger.debug("'%s: %s'" % (event_source_path, new_state))
    # Switch handler for various gang switches...
    # (kept minimal - original had many sound/play triggers)
    return "aye"
