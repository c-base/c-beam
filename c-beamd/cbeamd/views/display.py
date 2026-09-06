"""
Dashboards, displays and misc. widgets.

Split out of the original views.py; function bodies are unchanged.
"""

import os
import random
import re
from datetime import date

import feedparser
import requests
from django.contrib.auth.decorators import login_required
from django.http import HttpResponse
from django.shortcuts import render
from django.utils import timezone
from ..json_rpc_client import jsonrpc_method

from ..models import LTE, ActivityLog
from ..tools.ddate import DDate

from .helpers import ampelrpc, cerebrum_state, hand, logger, monitord, nerdctrl_cout
from .bar import get_barstatus
from .helpers import publish, userlist_with_online_percentage


@jsonrpc_method('lte')
def lte(request, user, args):
    args = args.split(' ')
    if len(args) >= 2:
        if args[0] not in ('MO', 'DI', 'MI', 'DO', 'FR', 'SA', 'SO'):
            return 'err_unknown_day'
        if args[1] == '0':
            for lte in LTE.objects.filter(username=user, day=args[0]):
                LTE.objects.delete(lte)
            return 'lte_removed'
        eta = " ".join(args[1:])
        eta = re.sub(r'(\d\d):(\d\d)', r'\1\2', eta)
        ltes = LTE.objects.filter(username=user, day=args[0]).order_by('username')
        if len(ltes) > 0:
            for lte in ltes:
                lte.eta = eta
                lte.save()
        else:
            LTE(username=user, day=args[0], eta=eta).save()
        return 'lte_set'
    return "meh"


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


@jsonrpc_method("cerebrumNotify")
def cerebrumNotify(request, device_name, event_source_path, new_state):
    cerebrum_state[device_name][event_source_path] = new_state

    logger.debug("'%s: %s'" % (event_source_path, new_state))
    if event_source_path == '/schaltergang/1':
        nerdctrl_cout.play('clamp.mp3')
    if event_source_path == '/schaltergang/2':
        nerdctrl_cout.play('carbon.mp3')
    if event_source_path == '/schaltergang/3':
        nerdctrl_cout.play('cience.mp3')
    if event_source_path == '/schaltergang/4':
        nerdctrl_cout.play('creatv.mp3')
    if event_source_path == '/schaltergang/5':
        nerdctrl_cout.play('cultur.mp3')
    if event_source_path == '/schaltergang/6':
        nerdctrl_cout.play('com.mp3')
    if event_source_path == '/schaltergang/7':
        nerdctrl_cout.play('core.mp3')
    if event_source_path == '/schaltergang/8':
        nerdctrl_cout.announce('die schalter sind kein spielzeug!')
    if event_source_path == '/schaltergang/9':
        if new_state == 0:
            publish("nerdctrl/open", "https://www.c-base.org")
        elif new_state == 1:
            publish("nerdctrl/open", "https://logbuch.c-base.org/")
        elif new_state == 2:
            publish("nerdctrl/open", "http://c-flo.cbrp3.c-base.org/mainhall/")
        elif new_state == 3:
            publish("nerdctrl/open", "http://c-flo.cbrp3.c-base.org/events/")
    if event_source_path == '/schaltergang/10':
        if new_state == 0:
            publish("nerdctrl/open", "https://c-beam.cbrp3.c-base.org/c-base-map")
        elif new_state == 1:
            publish("nerdctrl/open", "http://cbag3.c-base.org/artefact")
        elif new_state == 2:
            publish("nerdctrl/open", "https://c-beam.cbrp3.c-base.org/missions")
        elif new_state == 3:
            publish("nerdctrl/open", "https://c-beam.cbrp3.c-base.org/weather")
    if event_source_path == '/schaltergang/11':
        if new_state == 0:
            # publish("nerdctrl/open", "http://c-beam.cbrp3.c-base.org/bvg")
            publish("nerdctrl/open", "https://weilsiedichlieben.de?id=8089019&bus=true&express=true&ferry=true&regional=true&suburban=true&subway=true&tram=true&value=Berlin+Jannowitzbr%C3%BCcke&when=5&results=8&fontSize=26&id=732538&bus=true&express=true&ferry=true&regional=true&suburban=true&subway=true&tram=true&value=Heinrich-Heine-Str.+%28U%29%2C+Berlin&when=5&results=8&fontSize=26")
        elif new_state == 1:
            publish("nerdctrl/open", "https://c-beam.cbrp3.c-base.org/sensors")
        elif new_state == 2:
            # publish("nerdctrl/open", "https://c-beam.cbrp3.c-base.org/rickshaw/examples/fixed.html")
            publish("nerdctrl/open", "http://c-flo.cbrp3.c-base.org/bar-status/")
        else:
            # publish("nerdctrl/open", "http://c-beam.cbrp3.c-base.org/nerdctrl")
            publish("nerdctrl/open", "http://c-flo.cbrp3.c-base.org/internet/")
    if event_source_path == '/schaltergang/12':
        if new_state == 0:
            publish("nerdctrl/open", "http://c-beam.cbrp3.c-base.org/ceitloch")
        elif new_state == 1:
            # publish("nerdctrl/open", "http://visibletweets.com/#query=@cbase&animation=2")
            publish("nerdctrl/open", "https://www.c-base.org")
        elif new_state == 2:
            publish("nerdctrl/open", "https://c-beam.cbrp3.c-base.org/reddit")
        else:
            publish("nerdctrl/open", "http://vimeo.com/cbase/videos")

    if event_source_path == '/schaltergang/13':
        nerdctrl_cout.tts('Julia', 'huch!')
        publish("nerdctrl/open", "http://map.norsecorp.com/")
    if event_source_path == '/schaltergang/14':
        nerdctrl_cout.tts('Julia', 'achtung! alles turisten und nonteknischen lookenpeepers! das komputermaschine ist nicht fuer der gefingerpoken und mittengraben!')
    if event_source_path == '/schaltergang/15':
        nerdctrl_cout.tts('Julia', 'finger weg!')
    if event_source_path == '/schaltergang/16':
        nerdctrl_cout.play('cantdo.mp3')
    if event_source_path == '/schaltergang/18':
        nerdctrl_cout.play('Spock_hat_keinen_Bock.mp3')
    if event_source_path == '/schaltergang/19':
        nerdctrl_cout.play('kommtihrelendendaten.mp3')
    if event_source_path == '/schaltergang/20':
        nerdctrl_cout.play('darth.mp3')
    if event_source_path == '/schaltergang/21':
        nerdctrl_cout.play('faszinierend.mp3')
    if event_source_path == '/schaltergang/22':
        nerdctrl_cout.play('zugangzummastercontrollprogramm.mp3')
    if event_source_path == '/schaltergang/23':
        nerdctrl_cout.tts('Julia', 'alles zweifelhafte muss angezweifelt werden')
    if event_source_path == '/schaltergang/30':
        nerdctrl_cout.tts('Julia', 'alle mann sofort in die zeitmaschine!')
    if event_source_path == '/schaltergang/17':
        nerdctrl_cout.tts('Julia', 'achtung, achtung, hier spricht der bordcomputer. huhu!')
    if event_source_path == '/schaltergang/26':
        if new_state == 0:
            if cerebrum_state[device_name]['/schaltergang/24'] == 0:
                nerdctrl_cout.play('rocket_countdown_short')


@jsonrpc_method('toggle_burningman')
def toggle_burningman(request):
    try:
        monitord.burningman("foo")
    except Exception:
        pass
    return HttpResponse("OK")


def nerdctrl(request):
    return render(request, 'cbeamd/nerdctrl.django', {})


def cbeamviewer(request):
    return render(request, 'cbeamd/cbeamviewer.django', {})


def weather(request):
    return render(request, 'cbeamd/weather.django', {})


def bvg(request):
    return render(request, 'cbeamd/bvg.django', {})


def welcome(request, user):
    return render(request, 'cbeamd/welcome.django', {'user': user})


def sensors(request):
    return render(request, 'cbeamd/sensors.django', {})


def fakelevels():
    levels = {}
    levels['oxygen'] = random.choice(['kritisch', 'bedenklich', 'N/A', 'ööhm'])
    levels['carbon'] = random.choice(['eher so mittel', 'kuschelig', '0.234254 CE/m^3'])
    levels['conscience'] = random.choice(['entspannt', 'erweitert', 'erheitert', 'passt schon'])
    return levels


def dash(request):
    al = ActivityLog.objects.order_by('-timestamp')[:20]
    rev = list(al)
    rev.reverse()
    return render(request, 'cbeamd/dash.django', {'activitylog': rev, 'users': userlist_with_online_percentage(), 'barstatus': get_barstatus(request), 'levels': fakelevels()})


def mechdisplay(request):
    return render(request, 'cbeamd/mechdisplay.django', {})


def he1display(request):
    return render(request, 'cbeamd/he1display.django', {})


def ceitlochclocc(request):
    return render(request, 'cbeamd/ceitloch.django', {})


def donut(request):
    return render(request, 'cbeamd/donut.django', {})


@jsonrpc_method('reddit')
def reddit(request):
    d = feedparser.parse('http://www.reddit.com/r/cbase/.rss')
    return render(request, 'cbeamd/reddit.django', {'entries': d['entries']})


@jsonrpc_method('barbutton')
def barbutton(request, pressed):
    publish("c-beam-pager/barbot", timezone.localtime(timezone.now()).strftime("%H:%M"))
    return "aye"


@jsonrpc_method('ampel')
def ampel(request, red, yellow, green):
    try:
        logger.debug(ampelrpc.ampel(red, yellow, green))
    except Exception:
        pass
    return "aye"


@jsonrpc_method('ampelblink')
def ampelblink(request, program):
    try:
        logger.debug(ampelrpc.ampel(program))
    except Exception:
        pass
    return "aye"


@jsonrpc_method('issues')
def issues(request):
    url = "https://api.github.com/repos/c-base/meta/issues?state=open"
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


@login_required
def ampel_web(request, location, color, state):
    payload = '{"%s": %d}' % (color, int(state))
    # payload = '{"red": 1, "yellow": 1, "green": 1}'
    # payload = '{"red": 1}'
    publish("ampel/%s" % location, str(payload))
