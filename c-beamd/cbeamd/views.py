# -*- coding: utf-8 -*-

import sys, traceback
from threading import Timer
from jsonrpc import jsonrpc_method
from .models import User
from .models import LTE
from .models import Mission, Subscription, UserStatsEntry, MissionLog, Activity, ActivityLog, ActivityLogComment, Status
from datetime import datetime, timedelta, date
from django.utils import timezone
from jsonrpc.proxy import ServiceProxy
import cbeamdcfg as cfg
from urllib.request import urlopen
#from urllib import urlopen
import csv
from ics import Calendar

from django.template import Context, loader
from django.http import HttpResponse,HttpResponseRedirect
from django.shortcuts import render_to_response, get_object_or_404, render
from django.contrib.auth import login as login_auth
from django.contrib.auth import logout as logout_auth
from django.contrib.auth import authenticate
from .forms import LoginForm, MissionForm, StripeForm, UserForm, LogActivityForm, ActivityLogCommentForm
from django.template.context import RequestContext
from django.contrib.auth.decorators import login_required, user_passes_test
#from django.core.context_processors import csrf
from django.template.context_processors import csrf

from django.views.decorators.csrf import csrf_exempt
from gcm import GCM
import json
import logging

from random import choice

from .tools.ddate import DDate
from .tools.handTranslate import HandTranslate
#from .tools import crypto
from .tools.MyHTMLParser import MyHTMLParser
from .tools.LEDStripe import *

import paho.mqtt.client as paho
import string

import os, re, feedparser, json, random, ssl


import smtplib
from email.mime.text import MIMEText

### from tools.ldapNrf24 import LdapNrf24Check
#import urllib2
from mpd import MPDClient
from django_ajax.decorators import ajax

logger = logging.getLogger('cbeam')
hysterese = 15
eta_timeout=120

mqtt = paho.Client("c-beam")
mqttserver = "127.0.0.1"
cout = ServiceProxy('http://shout.cbrp3.c-base.org:1775/')
ampelrpc = ServiceProxy('http://10.0.1.24:1337/')
nerdctrl_cout = ServiceProxy('http://nerdctrl.cbrp3.c-base.org:1775/')
cerebrum = ServiceProxy('http://10.0.1.27:7777/')
portal = ServiceProxy('https://c-portal.c-base.org/rpc/')
monitord = ServiceProxy('http://10.0.1.27:9090/')
c_leuse_c_out = ServiceProxy('http://10.0.1.27:1775/')
culd = ServiceProxy('http://10.0.1.27:4339/')
apikey = 'AIzaSyBLk_iU8ORnHM39YQCUsHngMfG85Rg9yss'
artefact_base_url = "http://[2a02:f28:4::6b39:2d00]/artefact/"

newarrivallist = {}
newetalist = {}
newactivities = []
achievements = {}

eventcache = []
eventdetailcache = []
eventcache_time = timezone.now() - timedelta(days=1)
event_details = []

artefactcache = {}
artefactcache_time = timezone.now() - timedelta(days=1)

cerebrum_state = {}
cerebrum_state['nerdctrl'] = {}

hwstorage_state = "closed"

default_stripe_pattern = 4
default_stripe_speed = 3
default_stripe_offset = 0

# mission states
mission_open = "open"
mission_assigned = "assigned"
mission_completed = "completed"

c_out_volume = 0

hand = HandTranslate()

def AddPadding(data, interrupt, pad, block_size):
    new_data = ''.join([data, interrupt])
    new_data_len = len(new_data)
    remaining_len = block_size - new_data_len
    to_pad_len = remaining_len % block_size
    pad_string = pad * to_pad_len
    return ''.join([new_data, pad_string])

def StripPadding(data, interrupt, pad):
    return data.rstrip(pad).rstrip(interrupt)

def reply(request, text):
    if request.path.startswith('/rpc'):
        return text
    else:
        return HttpResponse(text)

#################################################################
# Login / Logout
#################################################################

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
    login in to c-beam ignoring the current online state
    """
    u = getuser(user)
    welcometts(request, u.username)
    try:
        monitord.login(u.username)
    except:
        pass
    if not u.no_google:
        try: gcm_send(request, 'now boarding', u.username)
        except: pass
    payload = {'user': str(u.username), 'timestamp': timezone.localtime(timezone.now()).strftime("%H:%M")}
    publish("user/boarding", json.dumps(payload))

    #publish("nerdctrl/open", "https://c-beam.cbrp3.c-base.org/welcome/%s" % str(u.username))
    if u.status == "eta":
        u.eta = ""
    oldstatus = u.status
    u.status = "online"
    u.logintime=timezone.now()
    u.extendtime=timezone.now()
    u.save()
    log_stats()
    if u.logouttime + timedelta(minutes=60) < timezone.now() and oldstatus in ["offline", "eta"]:
         logactivity(request, user, "login", 1)
    newarrivallist[u.username] = timezone.now()
    return reply(request, "%s logged in" % u.username)

@jsonrpc_method('stealth_login')
def stealth_login(request, user):
    """
    log in to c-beam without text-to-speech greeting
    """
    u = getuser(user)
    if u.status == "eta":
        u.eta = ""
    u.status = "online"
    u.logintime=timezone.now()
    u.extendtime=timezone.now()
    u.save()
    log_stats()
    #logactivity(request, user, "login")
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
    u = getuser(user)
    try:
        monitord.logout(u.username)
    except:
        pass
    payload = {'user': str(u.username), 'timestamp': timezone.localtime(timezone.now()).strftime("%H:%M")}
    publish("user/leaving", json.dumps(payload))
    oldstatus = u.status
    u.status = "offline"
    u.logouttime = timezone.now()
    u.save()
    log_stats()
    if u.logintime + timedelta(minutes=60) < timezone.now() and oldstatus == "online":
        logactivity(request, user, "logout", 2)
    return reply(request, "%s logged out" % u.username)

@login_required
def logout_web(request):
    result = force_logout(request, request.user.username)
    return render(request, 'cbeamd/c_buttons.django', {'result': 'du wurdest abgemeldet'})


#jsonrpc_method('login_wlan')
@jsonrpc_method('wifi_login')
def login_wlan(request, user):
    """
    login to c-beam via wifi
    """
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
    if is_logged_in(user): # TODO and logintimeout
        return logout(request, user)
    else:
        return login(request, user)

@jsonrpc_method('unknown_tag')
def unknown_tag(request, rfid):
    u = User.objects.filter(rfid__icontains=rfid)
    if len(u) > 0:
        return tagevent(request, u[0].username)
    else:
        return monmessage(request, rfid)


def welcometts(request, user):
    #if os.path.isfile('%s/%s/hello.mp3' % (cfg.sampledir, user)):
    #    os.system('mpg123 %s/%s/hello.mp3' % (cfg.sampledir, user))
    #else:
    if getnickspell(request, user) != "NONE":
        if user == "kristall":
            tts(request, "Julia", "a loa crew")
        else:
            tts(request, "Julia", cfg.ttsgreeting % getnickspell(request, user))

#################################################################
# User Handling
#################################################################

def getuser(user):
    user = user.lower().rstrip()
    if user == "nielc": user = "keiner"
    if user == "azt": user = "pille"
    try:
        u = User.objects.get(username=user)
    except:
        u = User(username=user, logintime=timezone.now()-timedelta(seconds=hysterese), extendtime=timezone.now()-timedelta(seconds=hysterese), logouttime=timezone.now()-timedelta(seconds=hysterese), status="unknown")
        u.save()
    return u

def getuser_eta(user):
    user = user.lower().rstrip()
    if user == "nielc": user = "keiner"
    if user == "azt": user = "pille"
    try:
        u = User.objects.get(username=user)
    except:
        return None
    return u

@jsonrpc_method('get_user_by_id')
def get_user_by_id(request, id):
    """
    get information about a user using his id
    """
    u = User.objects.get(id=id)
    return u.dic()

@jsonrpc_method('get_user_by_name')
def get_user_by_id(request, username):
    """
    get information about a user using his nickname
    """
    u = User.objects.get(username=username)
    return u.dic()

@jsonrpc_method('getnickspell')
def getnickspell(request, user):
    u = getuser(user)
    if u.nickspell == "":
        return user
    else:
        return u.nickspell

@jsonrpc_method('setnickspell')
def setnickspell(request, user, nickspell):
    u = getuser(user)
    u.nickspell = nickspell
    u.save()
    return "ok"

@jsonrpc_method('setwlanlogin')
def setwlanlogin(request, user, enabled):
    u = getuser(user)
    u.wlanlogin = enabled
    u.save()

@jsonrpc_method('getwlanlogin')
def getwlanlogin(request, user):
    u = getuser(user)
    return u.wlanlogin

def is_logged_in(user):
    if user == "nielc": user = "keiner"
    if user == "azt": user = "pille"
    return len(User.objects.filter(username=user, status="online")) > 0

@jsonrpc_method('get_autologout')
def get_autologout(request, user):
    u = getuser(user)
    return u.autologout

@jsonrpc_method('set_autologout')
def set_autologout(request, user, autologout):
    u = getuser(user)
    u.autologout = autologout
    u.save()
    return "aye"

def userlist():
    return [str(user) for user in User.objects.filter(status="online").order_by('username')]

def userlist_with_online_percentage():
    return [str(user)+" ("+user.online_percentage()+"%)" for user in User.objects.filter(status="online").order_by('username')]

@jsonrpc_method('available')
def available(request):
    cleanup(request)
    return userlist()

def ceitloch():
    now = int(timezone.now().strftime("%Y%m%d%H%M%S"))
    cl = {}
    for user in User.objects.filter(status="online"):
        td = timezone.now() - user.logintime
        cl[str(user)] = td.seconds
    return cl

def etalist():
    result = {}
    for u in User.objects.filter(status="eta").order_by('username'):
        result[u.username] = u.eta
    return result

@jsonrpc_method('who')
def who(request):
    """list all user that have logged in."""
    cleanup(request)
    return {'available': userlist(), 'eta': etalist(), 'etd': [], 'lastlocation': {}, 
            'ceitloch': ceitloch(), 'reminder': reminder()}


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
    #TODO
    #if text[:2].upper() in weekdays:
        #return lte(bot, ievent)

    if text in ('gleich', 'bald', 'demnaechst', 'demnächst', 'demn\xe4chst'):
        etaval = datetime.now() + timedelta(minutes=30)
        eta = etaval.strftime("%H%M")
    elif text.startswith('+'):
        foo = int(text[1:])
        etaval = datetime.now() + timedelta(minutes=foo)
        eta = etaval.strftime("%H%M")
    #elif ievent.rest == 'heute nicht mehr':
     #   eta = "0"
    else: 
        eta = text   
    # remove superflous colons
    eta = re.sub(r'(\d\d):(\d\d)',r'\1\2',eta)
    #eta = re.sub(r'(\d\d).(\d\d)',r'\1\2',eta)

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
    #data['newetas'][user] = eta

    u = getuser_eta(user)
    if u is None:
        return "you do not exist"

    newetalist[user] = eta
    if eta == '0':
        # delete eta for user
        u.eta=""
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
            try: gcm_send(request, 'ETA', '%s (%s)' % (user, eta))
            except: pass
        payload = {'user': str(u.username), 'timestamp': timezone.localtime(timezone.now()).strftime("%H:%M"), 'eta': eta}
        publish("user/eta", json.dumps(payload))
        #publish("user/eta", '%s (%s)' % (user, eta))
        log_stats()
        return 'eta_set'

def extract_eta(text):
    m = re.match(r'^.*?(\d\d\d\d).*', text)
    if m:
        return m.group(1)
    else:
        return "9999"

#################################################################
# Subscription & achievement handling
#################################################################

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
    global newetalist
    tmp = newetalist
    newetalist = {}
    return tmp

@jsonrpc_method('arrivals')
def arrivals(request):
    global newarrivallist
    tmp = newarrivallist
    newarrivallist = {}
    return tmp

@jsonrpc_method('achievements')
def achievements(request):
    global achievements
    tmp = achievements
    achievements = {}
    return tmp

@jsonrpc_method('activities')
def activities(request):
    global newactivities
    tmp = newactivities
    newactivities = []
    return tmp

#################################################################
# Cleanup methods
#################################################################

@jsonrpc_method('cleanup')
def cleanup(request):
    users = userlist()
    usercount = len(users)
    autologout = False

    now = int(timezone.now().strftime("%Y%m%d%H%M%S"))

    # remove expired users
    for u in User.objects.filter(status="online"):
        #if u.logintime + timedelta(minutes=cfg.timeoutdelta) < timezone.now():
        if u.autologout_in() <= 0:
            autologout = True
            u.status="offline"
            u.logouttime = timezone.now()
            u.save()
            log_stats()

    # remove expired ETAs
    for u in User.objects.filter(status="eta"):
        if u.etatimestamp < timezone.now():
            u.eta=""
            u.status = "offline"
            u.save()
            log_stats()

    # remove expired ETDs

    if autologout:
        set_stripe_default(request)

    for mission in Mission.objects.filter(status="completed").filter(repeat_after_days__gte=0):
        if mission.completed_on + timedelta(mission.repeat_after_days) > timezone.now():
            mission.status = "open"
            mission.save()

    return "aye"


#################################################################
# event methods
#################################################################

@jsonrpc_method('events')
def events(request):
    """
    get todays events
    """
    global eventcache
    update_event_cache()
    return eventcache

@jsonrpc_method('event_list')
def event_list(request):
    """
    get todays events with details
    """
    global eventdetailcache
    update_event_cache()
    return eventdetailcache

@jsonrpc_method('event_detail')
def event_detail(request, id):
    """
    get details for event with id id
    """
    d = feedparser.parse('http://www.c-base.org/calender/phpicalendar/rss/rss2.0.php?cal=&cpath=&rssview=today')
    #d = feedparser.parse('https://www.c-base.org/calender/phpicalendar/rss/rss2.0.php?cal=&cpath=&rssview=month')
    for entry in d['entries']:
        title = re.search(r'.*: (.*)', entry['title']).group(1)
        end = re.search(r'(\d\d\d\d-\d\d-\d\d)T(\d\d:\d\d):(\d\d)', entry['ev_enddate']).group(2).replace(':', '')
        start = re.search(r'(\d\d\d\d-\d\d-\d\d)T(\d\d:\d\d):(\d\d)', entry['ev_startdate']).group(2).replace(':', '')
        title = title.replace("c   user", "c++ user")
        #events.append('%s (%s-%s)' % (title, start, end))
    return "aye"

def update_event_cache():
    global eventcache_time
    global eventcache
    global eventdetailcache
    if eventcache_time.day == timezone.now().day:
        return
    events = []
    event_details = []
    #try:
        #d = feedparser.parse('https://www.c-base.org/calendar/exported/c-base-events.ics')
        #d = feedparser.parse('https://www.c-base.org/calender/phpicalendar/rss/rss2.0.php?cal=&cpath=&rssview=month')
        #d = feedparser.parse('http://www.c-base.org/calender/phpicalendar/rss/rss2.0.php?cal=&cpath=&rssview=today')
    #except:
        #pass

    url = 'https://www.c-base.org/calendar/exported/c-base-events.ics'
    c = Calendar(urlopen(url).read().decode('utf-8'))

    if c is not None:
        for entry in c.events: # d['entries']:
            entryid = 42
            try:
                #entryid = re.search(r'.*&uid=(.*)@google.com', entry['id']).group(1)
                entryid = entry.uid # re.search(r'.*&uid=(.*)', entry['id']).group(1)
            except: pass


            title = entry.name # re.search(r'.*: (.*)', entry['title']).group(1)
            end = re.search(r'(\d\d\d\d-\d\d-\d\d)T(\d\d:\d\d):(\d\d)', str(entry.end)).group(2).replace(':', '')
            #end = re.search(r'(\d\d\d\d-\d\d-\d\d)T(\d\d:\d\d):(\d\d)', entry['ev_enddate']).group(2).replace(':', '')
            start = re.search(r'(\d\d\d\d-\d\d-\d\d)T(\d\d:\d\d):(\d\d)', str(entry.begin)).group(2).replace(':', '')
            #start = re.search(r'(\d\d\d\d-\d\d-\d\d)T(\d\d:\d\d):(\d\d)', entry['ev_startdate']).group(2).replace(':', '')
            title = title.replace("c   user", "c++ user")
            if str(entry.begin).startswith(date.today().strftime("%Y-%m-%d")):
                description = entry.description # ['summary_detail']['value']
                events.append('%s (%s-%s)' % (title, start, end))
                event_details.append({'id': entryid, 'title':title, 'start': start, 'end': end, 'description': description})
        eventcache = events
        eventdetailcache = event_details
        eventcache_time = timezone.now()

def event_list_web(request):
    return render(request, 'cbeamd/event_list.django', {'event_list': event_list(request)})

#################################################################
# scanner methods
#################################################################

@jsonrpc_method('monmessage')
def monmessage(request, message):
    """
    display message on the display in the airlock (c_leuse)
    """
    try:
        monitord.message(message)
    except:
        pass
    return "yo"

#################################################################
# c_out methods
#################################################################

@jsonrpc_method('tts')
def tts(request, voice, text):
    """
    perform text-to-speech over c_out with voice saying text
    """
    result = "aye"
    #try:
        #result = cout.tts(voice, text)
    #except:
        #pass
    return result

@jsonrpc_method('r2d2')
def r2d2(request, text):
    """
    perform text-to-r2d2 over c_out with voice saying text
    """
    return cout.r2d2(text)

@jsonrpc_method('play')
def play(request, file):
    """
    play sound file via c_out
    """
    result = "aye"
    if file == '':
        publish("c_out/loop", "")
    else:
        publish("c_out/play", str(file))
    #try:
        #result = cout.play(file)
    #except:
        #pass
    return result

@jsonrpc_method('setvolume')
def setvolume(request, volume):
    """
    set c_out volume to volume
    """
    return cout.setvolume(volume)

@jsonrpc_method('getvolume')
def getvolume(request, volume):
    """
    get the current c_out volume
    """
    return cout.getvolume(volume)

@jsonrpc_method('voices')
def voices(request):
    """
    get a list of available voices for text-to-speech
    """
    return cout.voices()

@jsonrpc_method('sounds')
def sounds(request):
    """
    returns a list of sounds available to play via c_out
    """
    result = []
    try: result = sorted(cout.sounds()['result'])
    except: pass
    return result

@jsonrpc_method('c_out')
def c_out(request):
    """
    plays a random sound via c_out
    """
    return cout.c_out()

@jsonrpc_method('announce')
def announce(request, text):
    """
    perform a text-to-speech announcement via c_out
    """
    result = "aye"
    publish("c_out/announce", str(text))
    try:
        result = cout.announce(text)
    except:
        pass
    return result

@login_required
def c_out_web(request):
    return render(request, 'cbeamd/c_out.django', {'sound_list': sounds(request)})

@login_required
def c_out_play_web(request, sound):
    result = play(request, sound)
    return render(request, 'cbeamd/c_out.django', {'sound_list': sounds(request), 'result': "sound wurde abgespielt"})



#################################################################
# ToDo
#################################################################

#def todo():
#    todoarray = []
#    try:
#        todos = eval(open(cfg.todofile).read())
#        for item in todos['list']:
#            todoarray.append(item['txt'])
#    except: pass
#
#    return todoarray
#################################################################
# DHCP hook
#################################################################

#def dhcphook(action, mac, ip, name):
    #if data['macmap'].has_key(mac):
        #user = data['macmap'][mac]
        #save()
        #if user in userlist():
        #else:            login(user)
    #return
#def addmac(user, mac):
    #data['macmap'][mac] = user
    #save()
    #return "aye"
#
#def delmac(user, mac):
    #if data['macmap'][mac] == user:
        #del data['macmap'][mac]        save()
        #return "aye"
    #else:
        #return "die mac %s ist %s nicht zugeordnet" % (mac, user)

#################################################################
# r0ket methods
#################################################################

### # cbeam.r0ketSeen(result.group(1), sensor, result.group(2), result.group(3))
### @jsonrpc_method('r0ketseen')
### def r0ketseen(request, r0ketid, sensor, payload, signal):
###     timestamp = 42
###     user = getr0ketuser(request, r0ketid)
###     if user:
### #    if r0ketid in data['r0ketids'].keys():
### #        #data['r0ketmap'][r0ketid] = [sensor, payload, signal, timestamp]
### #        data['lastlocation'][user] = sensor
###         result = login_wlan(request, user)
###     else:
###         print('saw unknown r0ket: %s (%s)' % (r0ketid, sensor))
### #    save()
###     return "aye"
### #
### #def getr0ketmap():
### #    return data['r0ketmap']
### #
### #def registerr0ket(r0ketid, user):
### #    data['r0ketids'][r0ketid] = user
### #    save()
### #    return "aye"
### #
### @jsonrpc_method('getr0ketuser')
### def getr0ketuser(request, r0ketid):
###     f = LdapNrf24Check("ldap://10.0.1.7:389/", 'ou=crew,dc=c-base,dc=org', '', '', 'nrf24', '(memberOf=cn=crew,ou=groups,dc=c-base,dc=org)')
###     m = re.search("uid=(.*?),ou.*", f.getUserForNrf24(r0ketid))
###     return m.group(1)
###     #return "ID: "+f.getUserForNrf24(r0ketid)
###     #return data['r0ketids'][r0ketid]

#################################################################
# reminder methods
#################################################################

@jsonrpc_method('remind')
def remind(user, reminder):
   u = getuser(user)
   u.reminder = reminder
   return "aye"

def reminder():
    result = {}
    for u in User.objects.filter(status="eta"):
        result[u.username] = u.reminder
    return result

#################################################################
# LTE methods
#################################################################

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
        eta = re.sub(r'(\d\d):(\d\d)',r'\1\2', eta)
        ltes = LTE.objects.filter(username=user, day=args[0]).order_by('username')
        if len(ltes) > 0:
            for lte in ltes:
                lte.eta = eta
                lte.save()
        else:
            LTE(username=user, day=args[0], eta=eta).save()
        return 'lte_set'
    return "meh"

#
#def getlteforday(day):
#    if day in ('MO', 'DI', 'MI', 'DO', 'FR', 'SA', 'SO'):
#        return LTE.objects.filter(day=day)
#    else:
#        return 'err_unknown_day'
#
#def getlte():
#        return data['ltes']


#################################################################
# Web Views
#################################################################

def index2(request):
    online_users_list = User.objects.filter(status="online").order_by('username')
    eta_list = User.objects.filter(status="eta").order_by('username')
    #event_list = 
    t = loader.get_template('cbeamd/index.django')
    c = Context({
         'online_users_list': online_users_list,
         "eta_list": eta_list,
    })
    return HttpResponse(t.render(c))

@login_required
def index(request):
    user_list_online = User.objects.filter(status="online").order_by('username')
    user_list_eta = User.objects.filter(status="eta").order_by('username')
    user_list_offline = User.objects.filter(status="offline").order_by('username')
    al = ActivityLog.objects.order_by('-timestamp')[:20]
    rev = list(al)
    rev.reverse()
    return render(request, 'cbeamd/index.django', {'user_list_online': user_list_online, 'user_list_eta': user_list_eta, 'user_list_offline': user_list_offline, 'status': 'all', 'activitylog': rev})

@login_required
def user(request, user_id):
    u = get_object_or_404(User, pk=user_id)
    return render(request, 'cbeamd/user_detail.django', {'user': u})

@login_required
def user_online(request):
    user_list = User.objects.filter(status="online").order_by('username')
    return render(request, 'cbeamd/user_list.django', {'user_list': user_list, 'status': 'online'})

@login_required
def user_offline(request):
    user_list = User.objects.filter(status="offline").order_by('username')
    return render(request, 'cbeamd/user_list.django', {'user_list': user_list, 'status': 'offline'})

@login_required
def user_eta(request):
    user_list = User.objects.filter(status="eta").order_by('username')
    return render(request, 'cbeamd/user_list.django', {'user_list': user_list, 'status': 'eta'})

@login_required
def user_all(request):
    user_list_online = User.objects.all().order_by('username')
    return render(request, 'cbeamd/user_list.django', {'user_list': user_list, 'status': 'all'})

@login_required
def user_list_web(request):
    user_list_online = User.objects.filter(status="online").order_by('username')
    user_list_eta = User.objects.filter(status="eta").order_by('username')
    user_list_offline = User.objects.filter(status="offline").order_by('username')
    return render(request, 'cbeamd/user_list.django', {'user_list_online': user_list_online, 'user_list_eta': user_list_eta, 'user_list_offline': user_list_offline, 'status': 'all'})

@jsonrpc_method('user_list')
def user_list(request):
    users = User.objects.all().order_by('username')
    return [user.dic() for user in users]

@jsonrpc_method('stats_list')
def stats_list(request):
    #user_list = User.objects.filter(stats_enabled=True).exclude(ap=0).order_by('-ap', 'username')
    user_list = sorted(list(User.objects.filter(stats_enabled=True).exclude(ap=0)), key=lambda x: x.calc_ap(), reverse=True)
    return [user.dic() for user in user_list]

@login_required
def stats(request):
    #user_list = User.objects.filter(stats_enabled=True).exclude(ap=0).order_by('-ap', 'username')
    user_list = sorted(list(User.objects.filter(stats_enabled=True).exclude(ap=0)), key=lambda x: x.calc_ap(), reverse=True)
    return render(request, 'cbeamd/stats.django', {'user_list': [user.dic() for user in user_list]})


@login_required
def control(request):
    return render(request, 'cbeamd/control.django', {})

@login_required
def c_leuse(request):
    return render(request, 'cbeamd/c_leuse.django', {})

@login_required
def c_buttons(request):
    return render(request, 'cbeamd/c_buttons.django', {})

@login_required
def profile_edit(request):
    if request.method == "POST":
        u = getuser(request.user.username)
        form = UserForm(request.POST, instance=u)
        #m = Mission.objects.get(pk=mission_id)
        #form = MissionForm(request.POST, instance=m)
        if form.is_valid():
            form.save()
            #return HttpResponseRedirect('/missions/%s' % mission_id)
    else:
        u = getuser(request.user.username)
        form = UserForm(instance=u)
    return render(request, 'cbeamd/user_form.django', locals())


#################################################################
# Web Login / Logout
#################################################################

#def auth_login( request ):
#    redirect_to = request.GET.get( 'next', '' ) or '/'
#    if request.method == 'POST':
#        form = LoginForm( request.POST )
#        if form.is_valid():
#            username = form.cleaned_data['username']
#            password = form.cleaned_data['password']
#            user = authenticate( username=username, password=password )
#            if user is not None:
#                if user.is_active:
#                    login_auth( request, user )
#                    return HttpResponseRedirect( redirect_to )
#    else:
#        form = LoginForm()
#    return render(request,  'cbeamd/login.django', locals()) #, context_instance = RequestContext(request))
#
#def auth_logout( request ):
#    redirect_to = request.GET.get( 'next', '' ) or '/'
#    logout_auth( request )
#    return HttpResponseRedirect( redirect_to )

#################################################################
# mission handling
#################################################################

@jsonrpc_method('add_mission')
def add_mission(request, short_description):
    """
    add a new mission with a short_description
    """
    m = Mission(short_description=short_description)
    m.save()
    return "aye"

@jsonrpc_method('missions')
def missions(request):
    """
    returns a list of available missions
    """
    return [str(mission) for mission in Mission.objects.order_by('status', 'short_description')]

@jsonrpc_method('mission_detail')
def mission_detail(request, mission_id):
    """
    returns the details for the mission specified with mission_id
    """
    mission = get_object_or_404(Mission, pk=mission_id)
    return mission.dic()
    #return render(request, 'cbeamd/mission_detail.django', {'mission': mission})

@jsonrpc_method('mission_assign')
def mission_assign(request, user, mission_id):
    """
    assign the mission with mission_id to user
    """
    u = getuser(user)
    m = Mission.objects.get(id=mission_id)
    if m.status == mission_open or m.status == mission_assigned:
        m.assigned_to.add(u)
        m.status = mission_assigned
        m.save()
        return "success"
    return "mission not available"

@jsonrpc_method('mission_cancel')
def mission_cancel(request, user, mission_id):
    """
    cancel the mission with mission_id for user
    """
    u = getuser(user)
    m = Mission.objects.get(id=mission_id)
    if u in m.assigned_to.all() and m.status == mission_assigned:
        m.assigned_to.remove(u)
        if m.assigned_to.count() <= 0:
            m.status = mission_open
        m.save()
        return "success"
    return "not assigned to user"

@jsonrpc_method('mission_complete')
def mission_complete(request, user, mission_id):
    """
    complete the mission with mission_id for user
    """
    u = getuser(user)
    m = Mission.objects.get(id=mission_id)
    if u in m.assigned_to.all() and m.status == mission_assigned:
        #m.assigned_to.clear()
        m.assigned_to.remove(u)
        if m.assigned_to.count() <= 0:
            if m.repeat_after_days == 0:
                m.status = mission_completed
            else:
                m.status = mission_open
        m.save()
        if u.stats_enabled:
            al = ActivityLog()
            al.user = u
            al.ap = m.ap
            al.activity = Activity.objects.get(activity_type="mission completed")
            al.mission = m
            al.save()
            #u.ap = u.ap + m.ap
            u.ap = u.calc_ap()
            u.save()
            if not u.no_google:
                try: gcm_send_mission(request, "mission completed", al.notification_str())
                except: pass
            publish("mission/completed", str(al.notification_str()))

        return "success"
    return "failure"

@login_required
def mission_assign_web(request, mission_id):
    missions_available = Mission.objects.filter(status="open").order_by('short_description')
    missions_in_progress = Mission.objects.filter(status="assigned").order_by('short_description')
    cuser = getuser(request.user.username),
    result = mission_assign(request, request.user.username, mission_id)
    if result == "success":
        result = "Mission erfolgreich gestartet"
    else:
        result = "Mission konnte nicht gestartet werden"
    return render(request, 'cbeamd/mission_list.django', locals())

@login_required
def mission_complete_web(request, mission_id):
    missions_available = Mission.objects.filter(status="open").order_by('short_description')
    missions_in_progress = Mission.objects.filter(status="assigned").order_by('short_description')
    cuser = getuser(request.user.username),
    result = mission_complete(request, request.user.username, mission_id)
    if result == "success":
        result = "Mission erfolgreich abgeschlossen"
    else:
        result = "Mission konnte nicht abgeschlossen werden"
    return render(request, 'cbeamd/mission_list.django', locals())

@login_required
def mission_cancel_web(request, mission_id):
    missions_available = Mission.objects.filter(status="open").order_by('short_description')
    missions_in_progress = Mission.objects.filter(status="assigned").order_by('short_description')
    cuser = getuser(request.user.username),
    result = mission_cancel(request, request.user.username, mission_id)
    if result == "success":
        result = "Mission erfolgreich abgebrochen"
    else:
        result = "Mission konnte nicht abgebrochen"

    return render(request, 'cbeamd/mission_list.django', locals())


#@login_required
@jsonrpc_method('mission_list')
def mission_list(request):
    """
    returns a list of available missions
    """
    if request.path.startswith('/rpc'):
        missions = Mission.objects.order_by('-status', 'short_description')
        return [mission.dic() for mission in missions]
    else:
        missions_available = Mission.objects.filter(status="open").order_by('short_description')
        missions_in_progress = Mission.objects.filter(status="assigned").order_by('short_description')
        cuser = request.user.username
        return render(request, 'cbeamd/mission_list.django', locals())

def is_mission_editor(user):
    return True

@login_required
@user_passes_test(is_mission_editor)
def edit_mission(request, mission_id):
    if request.method == "POST":
        m = Mission.objects.get(pk=mission_id)
        form = MissionForm(request.POST, instance=m)
        if form.is_valid():
            form.save()
            result = "Mission gespeichert"
            return render(request, 'cbeamd/mission_list.django', locals())
            #return HttpResponseRedirect('/missions/%s' % mission_id)
    else:
        m = Mission.objects.get(id=mission_id)
        form = MissionForm(instance=m)
    return render(request, 'cbeamd/mission_form.django', locals())

#################################################################
# Google Cloud Messaging
#################################################################

@jsonrpc_method('gcm_register')
def gcm_register(request, user, regid):
    s = Subscription()
    s.regid = regid
    s.user = getuser(user)
    s.save()
    return "aye"

@jsonrpc_method('gcm_update')
def gcm_update(request, user, regid):
    u = getuser(user)
    subs = Subscription.objects.filter(user=u)
    if len(subs) < 1:
        s = Subscription()
        s.regid = regid
        s.user = u
        s.save()
    else:
        s = subs[0]
        s.regid = regid
        s.save()
    return "aye"

# This method should usually not be exposed through JSON-RPC
# @jsonrpc_method('gcm_send')
def gcm_send(request, title, text):
    gcm = GCM(apikey)
    if title == "now boarding":
        users = User.objects.filter(push_boarding=True)
    elif title == "ETA":
        users = User.objects.filter(push_eta=True)
    elif title == "mission completed":
        users = User.objects.filter(push_missions=True,stats_enabled=True)
    else:
        #users = User.objects.all()
        users = []
        return
    now = timezone.localtime(timezone.now())
    timestamp = "%d:%d" % (now.hour, now.minute)
    subscriptions = Subscription.objects.filter(user__in=users)
    regids = [subscription.regid for subscription in subscriptions]
    data = {'title': title, 'text': text, 'timestamp': timestamp}
    response = gcm.json_request(registration_ids=regids, data=data)
    return response

def gcm_send_mission(request, title, text):
    gcm = GCM(apikey)
    users = User.objects.filter(stats_enabled=True,push_missions=True)
    #users = User.objects.filter(username="smile")
    subscriptions = Subscription.objects.filter(user__in=users)
    regids = [subscription.regid for subscription in subscriptions]
    data = {'title': title, 'text': text}
    response = gcm.json_request(registration_ids=regids, data=data)
    return response

@jsonrpc_method('gcm_send_test')
def gcm_send_test(request, title, text, username):
    gcm = GCM(apikey)
    u = getuser(username)
    now = timezone.localtime(timezone.now())
    timestamp = "%d:%d" % (now.hour, now.minute)
    subscriptions = Subscription.objects.filter(user=u)
    regids = [subscription.regid for subscription in subscriptions]
    data = {'title': title, 'text': text, 'timestamp': timestamp}
    response = gcm.json_request(registration_ids=regids, data=data)
    return response

#@jsonrpc_method('test_enc')
#def test_enc(request):
#    gcm = GCM(apikey)
#    encrypted_data = crypto.EncryptWithAES("fooderbar")
#    u = getuser("smile")
#    s = Subscription.objects.get(user=u)
#    regids = [s.regid]
#    data = {'title': "AES", 'text': encrypted_data}
#    response = gcm.json_request(registration_ids=regids, data=data)
#    return encrypted_data


@jsonrpc_method('smile', authenticated=True)
def smile(request):
    return "aye"

#################################################################
# CULd method forwarding
#################################################################

@jsonrpc_method('bluewall()')#, authenticated=True, validate=True)
def bluewall(request):
    #return culd.bluewall(True)
    return "culd not available"

@jsonrpc_method('darkwall()')#, authenticated=True, validate=True)
def darkwall(request):
    #return culd.darkwall(False)
    return "culd not available"

#@jsonrpc_method('hwstorage(Boolean)', authenticated=True, validate=True)
@jsonrpc_method('hwstorage')
def hwstorage(request):
    global timer
    #global hwstorage_state
    #if hwstorage_state == "open":
        #return
    #hwstorage_state = "open"
    #culd.hwstorage(True)
    #culd.hwstorage(True)
    def close():
        #culd.hwstorage(False)
        #culd.hwstorage(False)
        #hwstorage_state = "closed"
        pass
    timer = Timer(30.0, close)
    timer.start()
    return "aye"

def hwstorage_web(request):
    result = hwstorage(request, True)
    return render(request, 'cbeamd/c_buttons.django', {'result': 'Software-Endlager wurde geöffnet: %s' % result})

#################################################################
# artefact handling
#################################################################

@jsonrpc_method('artefact_list')
def artefact_list(request):
    """
    returns a list of available artefacts
    """
    global artefactcache
    global artefactcache_time
    global artefact_base_url
    artefactlist = {}
    if True: # artefactcache_time + timedelta(hours=1) < timezone.now():
        parser = MyHTMLParser()
        try:
            response = urlopen("http://10.0.1.44/artefact/").read().decode('utf-8')
            parser.feed(response)
            artefacts = parser.get_artefacts()
            artefactlist = [{'name': key, 'slug': artefacts[key]} for key in artefacts.keys()]
            artefactcache = artefactlist
            artefactcache_time = timezone.now()
        except Exception as e:
            logger.error(e)
            traceback.print_exc(file=sys.stdout)
    else:
        artefactlist = artefactcache
    # return sorted(artefactlist)
    return artefactlist

@jsonrpc_method('artefact_base_url')
def artefact_base_url(request):
    """
    returns the base URL for artefacts
    """
    global artefact_base_url
    return [artefact_base_url]


def artefact_list_web(request):
    return render(request, 'cbeamd/artefact_list.django', {'artefact_list': artefact_list(request)})

#################################################################
# article handling
#################################################################

@jsonrpc_method('list_articles')
def list_articles(request):
    """
    returns a list of c_portal articles
    """
    return portal.api.list_articles()


@jsonrpc_method('log_stats')
def log_stats():
    u = UserStatsEntry()
    u.usercount = len(User.objects.filter(status="online"))
    u.etacount = len(User.objects.filter(status="eta"))
    #u.save()
    return str(u)

@jsonrpc_method('get_stats')
def get_stats(request):
    """
    returns the currents user stats
    """
    return str(UserStatsEntry.objects.all())


#################################################################
# cerebrum leds methods
#################################################################

@jsonrpc_method('set_stripe_pattern')
def set_stripe_pattern(request, pattern_id):
    """
    set the airlock led stripe pattern to pattern_id
    """
    pattern_id = int(pattern_id)
    #if pattern_id == 0:
        #return cerebrum.partymode()
    #if pattern_id == 4:
        #return cerebrum.flimmer()
    if pattern_id == 7:
        return cerebrum.statics()
    if pattern_id == 3:
        patterns = cerebrum.get_patterns()['result']
        return cerebrum.set_pattern(random.choice(patterns))
    #if pattern_id < 20:
    result = cerebrum.set_pattern(pattern_id)
    #if pattern_id == 20:
        #result = cerebrum.flimmer()
    #if pattern_id == 21:
        #result = cerebrum.senso()
    #if pattern_id == 22:
        #result = cerebrum.blink()
    #if pattern_id == 23:
        #result = cerebrum.partymode()
    #if result['result'] == "aye":
        #result['result'] = "pattern has been set"
    #else:
        #result['result'] = "failed to set pattern"
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
    #buffer = [255,0,0,255,0,0,255,0,0,255,0,0,0,255,0,0,255,0,0,255,0,0,255,0,0,0,255,0,0,255,0,0,255,0,0,255,0,0,0,0,0,0,0,0,0,0,0,0]*32+[0,0,0,0,0,0,0,0,0,0,0,0]
    return cerebrum.set_buffer(buffer)

@jsonrpc_method('set_stripe_default')
def set_stripe_default(request):
    """
    set the airlock led stripe pattern to the default pattern
    """
    global default_stripe_pattern
    global default_stripe_speed
    global default_stripe_offset

    if len(User.objects.filter(status="online")) > 0:
        default_stripe_pattern = 1
        default_stripe_speed = 3
    else:
        default_stripe_pattern = 10
        default_stripe_speed = 1
    cerebrum.set_pattern(default_stripe_pattern)
    cerebrum.set_speed(default_stripe_speed)
    #cerebrum.set_offset(default_stripe_offset)
    return "aye"

@jsonrpc_method('notbeleuchtung')
def notbeleuchtung(request):
    """
    set the airlock led stripe pattern to emergency lights
    """
    global default_stripe_pattern
    global default_stripe_speed
    default_stripe_pattern = 10
    default_stripe_speed = 0
    cerebrum.set_pattern(10)
    cerebrum.set_speed(1)

@jsonrpc_method('rainbow')
def rainbow(request):
    """
    set the airlock led stripe pattern to rainbow
    """
    global default_stripe_pattern
    global default_stripe_speed
    default_stripe_pattern = 1
    default_stripe_speed = 3
    cerebrum.set_pattern(default_stripe_pattern)
    cerebrum.set_speed(default_stripe_speed)

#################################################################
# misc methods
#################################################################

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
    return "Today is "+str(now)

@jsonrpc_method('fnord')
def fnord(request):
    return DDate().fnord()


@jsonrpc_method('isWifiLoginEnabled()')
def isWifiLoginEnabled(request, users):
    return {user.username: user.wlanlogin for user in User.objects.filter(username__in=users)}

@jsonrpc_method('set_wlan_login')
def set_wlan_login(request, user, enabled):
    u = getuser(user)
    u.wlanlogin=enabled
    u.save()
    return "aye"

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

@jsonrpc_method('activitylog')
def activitylog(request):
    """
    returns the current c-game activitylog
    """
    al = ActivityLog.objects.order_by('-timestamp')[:40]
    rev = list(al)
    rev.reverse()
    return [ale.dic() for ale in rev]

@login_required
def activitylog_web(request):
    al = ActivityLog.objects.order_by('-timestamp')[:40]
    rev = list(al)
    rev.reverse()
    return render(request, 'cbeamd/activitylog.django', {'activitylog': rev})

@login_required
def activitylog_details_web(request, activitylog_id):
    activitylog = ActivityLog.objects.get(id=activitylog_id)
    return render(request, 'cbeamd/activitylog_details.django', locals())

@csrf_exempt
@login_required
def logactivity_web(request):
    u = getuser(request.user.username)
    if request.method == 'POST':
        form = LogActivityForm(request.POST)
        if form.is_valid():
            act = form.cleaned_data["activity"]
            ap = form.cleaned_data["ap"]
            logactivity(request, request.user.username, act, ap)
            return render(request, 'cbeamd/activitylog.django', {'form': form, 'result': 'SUCCESS'})
    #else:
        #form = StripeForm()
        #return render(request, 'cbeamd/stripe_form.django', {'form': form})

    return render(request, 'cbeamd/activitylog.django', {'result': 'FAIL'})

@jsonrpc_method('logactivity')
def logactivity(request, user, activity, ap):
    """
    log an activity for user with the description activity and ap activity points
    """
    global newactivities
    u = getuser(user)
    #u.ap = u.ap + ap
    if not u.stats_enabled:
        return "stats disabled for user"
    al = ActivityLog()
    al.user = u
    al.ap = int(ap)
    if activity == "login":
        al.activity = Activity.objects.get(activity_type="login")
    elif activity == "logout":
        al.activity = Activity.objects.get(activity_type="logout")
    else:
        act = Activity()
        act.activity_type = "custom"
        act.activity_text = activity
        act.save()
        al.activity = act
    al.save()
    u.ap = u.calc_ap()
    u.save()
    newactivities.append(al)
    return "aye"

def list_portal_articles():
    result = []
    #try: result = portal.api.list_articles()['result']
    #except: pass
    return result

@jsonrpc_method('app_data')
def app_data(request):
    """
    returns a large data structure that contains all current status information that is required by the c-beam app
    """
    missions = [mission.dic() for mission in  Mission.objects.order_by('-status', 'short_description')]
    return {'user': user_list(request), 'events': event_list(request), 'artefacts': artefact_list(request), 'missions': missions, 'activitylog': activitylog(request), 'stats': stats_list(request), 'barstatus': get_barstatus(request), 'articles': list_portal_articles(), 'sounds': sounds(request)}

@login_required
def activitylog_json(request):
    al = ActivityLog.objects.order_by('-timestamp')[:40]
    rev = list(al)
    rev.reverse()
    return HttpResponse(json.dumps([ale.dic() for ale in rev]), content_type="application/json")

def not_implemented(request):
    return render(request, 'cbeamd/not_implemented.django', {})

@login_required
def activitylog_post_comment(request, activitylog_id):
    result = "WTF"
    if request.method == 'POST':
        form = ActivityLogCommentForm(request.POST)
        activitylog = ActivityLog.objects.get(id=activitylog_id)
        u = getuser(request.user.username)
        users = [comment.user.username for comment in activitylog.comments.all()]
        if u.username in users:
            result = "commentar connte nicht gespeichert werden, du hast diese aktivita:t bereits commentiert"
        else:
            alc = ActivityLogComment()

            if form.is_valid():
                alc.comment = form.cleaned_data["comment"]
                alc.user = u
                if form.cleaned_data["protest"] == "protest":
                    activitylog.protests += 1
                    alc.comment_type = "protest"
                elif form.cleaned_data["thanks"] == "thanks":
                    activitylog.thanks += 1
                    alc.comment_type = "thanks"
                alc.save()
                activitylog.comments.add(alc)
                activitylog.save()
                result = "dance fu:r deinen commentar"
    return render(request, 'cbeamd/activitylog_details.django', locals())

@login_required
def activitylog_delete_comment(request, comment_id):
    alc = ActivityLogComment.objects.get(id=comment_id)
    u = getuser(request.user.username)
    if alc.user == u:
        alc.delete()

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
    volume = c_out_volume
    return render(request, 'cbeamd/c_out_volume.django', locals())


@login_required
def c_out_volume_json(request):
    return HttpResponse(json.dumps({'volume': c_out_volume}), content_type="application/json")

def c_out_volume_set(request, volume):
    global c_out_volume
    c_out_volume = volume
    return HttpResponse(json.dumps({'result': "OK"}), content_type="application/json")

@jsonrpc_method('barschnur')
def barschnur(request, pizza, sushi, inder):
    publish("bar/schnur", "%d, %d, %d" % (pizza, sushi, inder))

    if pizza == 0 and sushi == 1 and inder == 1:
        #publish("c_out/play", "pizza")
        publish("c_out/announce", "eine pizza-bestellung wartet an der bar")
    if pizza == 1 and sushi == 0 and inder == 1:
        #publish("c_out/play", "sushi")
        publish("c_out/announce", "eine sushi-bestellung wartet an der bar")
    if pizza == 1 and sushi == 1 and inder == 0:
        #publish("c_out/play", "inder")
        publish("c_out/announce", "eine inder-bestellung wartet an der bar")

@jsonrpc_method('c_portal.notify')
def c_portal_notify(request, notification):
    print(notification)

@jsonrpc_method("trafotron")
def trafotron(request, value):
    newval = (value * 100) / 170
    #print("trafotron: " + str(newval))
    #logger.error("trafotron: " + str(newval))
    #os.system("amixer -c 0 set Master %d%%" % newval)
    try:
        logger.debug(c_leuse_c_out.setvolume(newval))
    except Exception as e:
        logger.error(e)

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
            publish("nerdctrl/open", "http://www.c-base.org")
        elif new_state == 1:
            publish("nerdctrl/open", "http://logbuch.c-base.org/")
        elif new_state == 2:
            # publish("nerdctrl/open", "http://c-portal.c-base.org")
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
            publish("nerdctrl/open", "http://c-beam.cbrp3.c-base.org/bvg")
        elif new_state == 1:
            publish("nerdctrl/open", "https://c-beam.cbrp3.c-base.org/sensors")
        elif new_state == 2:
            #publish("nerdctrl/open", "https://c-beam.cbrp3.c-base.org/rickshaw/examples/fixed.html")
            publish("nerdctrl/open", "http://c-flo.cbrp3.c-base.org/bar-status/")
        else:
            # publish("nerdctrl/open", "http://c-beam.cbrp3.c-base.org/nerdctrl")
            publish("nerdctrl/open", "http://c-flo.cbrp3.c-base.org/internet/")
    if event_source_path == '/schaltergang/12':
        if new_state == 0:
            publish("nerdctrl/open", "http://c-beam.cbrp3.c-base.org/ceitloch")
        elif new_state == 1:
            # publish("nerdctrl/open", "http://visibletweets.com/#query=@cbase&animation=2")
            publish("nerdctrl/open", "http://c-base.org/")
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

@jsonrpc_method("barstatus")
def barstatus(request, status):
    """
    set the bar status to status
    status can be "open" or "closed"
    """
    status_object = Status.objects.get()
    if status == "open":
        status_object.bar_open = True
        status_object.save()
        notify_bar_opening()
    if status == "closed":
        status_object.bar_open = False
        status_object.save()
        notify_bar_closing()
    publish("bar/state", str(status), retain=True)

@jsonrpc_method("get_barstatus")
def get_barstatus(request):
    """
    get the current bar status
    """
    return Status.objects.get().bar_open

def notify_bar_opening():
    publish("bar/status", timezone.localtime(timezone.now()).strftime("%H:%M") + " bar opening")

def notify_bar_closing():
    publish("bar/status", timezone.localtime(timezone.now()).strftime("%H:%M") + " bar closing")

def publish(topic, payload, retain=False):
    try:
        mqtt.username_pw_set(cfg.mqtt_client_name, password=cfg.mqtt_client_password)
        if cfg.mqtt_server_tls:
            mqtt.tls_set(cfg.mqtt_server_cert, cert_reqs=ssl.CERT_OPTIONAL)
            mqtt.connect(cfg.mqtt_server, port=1884)
        else:
            mqtt.connect(cfg.mqtt_server, port=1883)

        mqtt.publish(topic, payload, qos=1, retain=retain)

    except Exception as e: 
        logger.error(e)
        pass

def create_random_password(length):
    chars = string.letters + string.digits
    return ''.join(choice(chars) for _ in range(length))

@jsonrpc_method('set_first_password')
def set_first_password(request, user):
    u = getuser(user)
    # u.tmp_password = create_random_password(16)
    # u.save()
    # send mail to "%s@c-base.org" % u.username including u.tmp_password
    recipient = '%s@c-base.org' % u.username 
    token = 'generierteseinmaltoken'
    text = 'hallo %s\n\n' % u.username
    text += '$jemand, wahrscheinlich du selbst, hat dein c-beam initialpasswort gesetzt.\n\nklicke auf den folgenden link, '
    text += 'um das passwort zu aktivieren:\n\n'
    text += 'https://ein-link-der-von-ueberall-erreichbar-sein-sollte.org/approve/%s\n\n' % token
    text += 'du solltest dein initialpasswort mo:glchst bald unter https://member.cbrp3.c-base.org und in der app a:ndern.\n\n'
    text += 'dance fu:r die beachtung der sicherheitshinweise\nihr bordcomputer\n\n'
    send_mail(recipient, text)

def send_mail(recipient, text):
    msg = MIMEText(text)
    msg['Subject'] = 'c-beam passwort gesetzt / c-beam password has been set'
    msg['From'] = "c-beam@c-base.org"
    msg['To'] = recipient

    s = smtplib.SMTP('localhost')
    s.sendmail("c-beam@c-base.org", [recipient], msg.as_string())
    s.quit()

    return "aye"

@jsonrpc_method('set_stealthmode')
def set_stealthmode(request, user, duration):
    """
    enable stealthmode for user for duration in hours
    """
    u = getuser(user)
    u.stealthmode = timezone.now() + timedelta(hours=duration)
    u.save()
    return "aye"

#@jsonrpc_method('get_stealthmode')
def get_stealthmode(request, user):
    u = getuser(user)
    return str(u.stealthmode)


@jsonrpc_method('toggle_burningman')
def toggle_burningman(request):
    try:
        monitord.burningman("foo")
    except:
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
    return levels;

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
    except: pass
    return "aye"

@jsonrpc_method('ampelblink')
def ampelblink(request, program):
    try:
        logger.debug(ampelrpc.ampel(program))
    except: pass
    return "aye"

@jsonrpc_method('issues')
def issues(request):
    url = "https://api.github.com/repos/c-base/meta/issues?state=open"
    issues = urllib2.urlopen(url).read()
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

def bar_preise(request):
    return render(request, 'cbeamd/bar_preise.django', {'prices': get_prices()})

def bar_leergut(request):
    return render(request, 'cbeamd/bar_leergut.django', {})

def bar_calc(request):
    return render(request, 'cbeamd/bar_calc.django', {'prices': get_prices()})

def bar_abrechnung(request):
    return render(request, 'cbeamd/bar_abrechnung.django', {})

def get_prices():
    prices = []
    with open('preise.csv', 'rb') as csvfile:
        pricereader = csv.reader(csvfile, delimiter=';', quotechar='"')
        for row in pricereader:
            prices.append(row)
    return prices

@login_required
def ampel(request, location, color, state):
    payload = '{"%s": %d}' % (color, int(state))
    #payload = '{"red": 1, "yellow": 1, "green": 1}'
    #payload = '{"red": 1}'
    publish("ampel/%s" % location, str(payload))
    

def mechblast_json(request):
    return HttpResponse(json.dumps({'userlist': userlist(), 'barstatus': get_barstatus(request)}), content_type="application/json")

def mpd_volume(request, host):
    with mpd_client(host) as client:
        if request.method == 'GET':
            result = {'volume': client.status()['volume']}
        elif request.method == 'POST':
            result = client.setvol(42)

    return HttpResponse(json.dumps(result), content_type="application/json")

@ajax
def mpd_status(request, host):
    result = {}
    with mpd_client(host) as client:
        result = client.status()
        result['current_song'] = client.currentsong()
        if 'title' not in result['current_song'].keys():
            result['current_song']['title'] = 'unknown'
        result['playlist'] = client.playlist()
        # 'time': '364:4535'
        elapsed = 0
        total = 0
        if 'time' in result.keys():
            (elapsed, total) = result['time'].split(':')
            result['elapsed'] = elapsed
            result['total'] = total
        else:
            result['elapsed'] = 0
            result['total'] = 0
    #return HttpResponse(json.dumps(result), content_type="application/json")
    return result


def mpd_play(request, host):
    with mpd_client(host) as client:
        result = client.play()
        return HttpResponse(json.dumps(result), content_type="application/json")

def mpd_stop(request, host):
    with mpd_client(host) as client:
        result = client.stop()
        return HttpResponse(json.dumps(result), content_type="application/json")

def mpd_command(request, host, command):
    result = {}
    with mpd_client(host) as client:
        if command == 'play':
            result = client.play()
        elif command == 'pause':
            result = client.pause()
        elif command == 'stop':
            result = client.stop()
        elif command == 'next':
            result = client.next()
        elif command == 'previous':
            result = client.previous()
        elif command == 'backward':
            result = client.seekcur("-10")
        elif command == 'forward':
            result = client.seekcur("+10")
        elif command == 'random':
            result = client.random(abs(mpd_get_random(host)-1))
        elif command == 'repeat':
            result = client.repeat(abs(mpd_get_repeat(host)-1))
        elif command == 'vol_up':
            result = client.setvol(mpd_get_volume(host)+5)
        elif command == 'vol_down':
            result = client.setvol(mpd_get_volume(host)-5)
    return HttpResponse(json.dumps(result), content_type="application/json")

def mpd_get_random(host):
    result = 0
    with mpd_client(host) as client:
        result = int(client.status()['random'])
    return result

def mpd_get_repeat(host):
    result = 0
    with mpd_client(host) as client:
        result = int(client.status()['repeat'])
    return result

def mpd_get_volume(host):
    result = 0
    with mpd_client(host) as client:
        result = int(client.status()['volume'])
    return result

@ajax
def mpd_listplaylists(request, host):
    result = {}
    with mpd_client(host) as client:
        result = client.listplaylists()
        #result = [item['playlist'] for item in result]
    #return HttpResponse(json.dumps(result), content_type="application/json")
    return result


class mpd_client():
    def __init__(self, host='localhost'):
        self.host = host
    def __enter__(self):
        self.client = MPDClient()
        self.client.timeout = 10
        self.client.connect(self.host, 6600)
        return self.client
    def __exit__(self, type, value, traceback):
        self.client.close()
        self.client.disconnect()
