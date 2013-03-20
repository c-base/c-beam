# -*- coding: utf-8 -*-

from threading import Timer
from jsonrpc import jsonrpc_method
from models import User
from models import LTE
from models import Mission, Subscription, UserStatsEntry
from datetime import datetime, timedelta, date
from django.utils import timezone
from jsonrpc.proxy import ServiceProxy
#from django.conf import settings
import cbeamdcfg as cfg
from ddate import DDate
from urllib import urlopen

from django.template import Context, loader
from django.http import HttpResponse,HttpResponseRedirect
from django.shortcuts import render_to_response, get_object_or_404
from django.contrib.auth import login as login_auth
from django.contrib.auth import logout as logout_auth
from django.contrib.auth import authenticate
from forms import LoginForm, MissionForm, StripeForm
from django.template.context import RequestContext
from django.contrib.auth.decorators import login_required
from django.core.context_processors import csrf
from django.views.decorators.csrf import csrf_exempt
from gcm import GCM
from LEDStripe import *

import os, re, feedparser

import crypto
from MyHTMLParser import MyHTMLParser

hysterese = 15
eta_timeout=120


cout = ServiceProxy('http://10.0.1.13:1775/')
cerebrum = ServiceProxy('http://10.0.1.27:7777/')
portal = ServiceProxy('https://c-portal.c-base.org/rpc/')
monitord = ServiceProxy('http://10.0.1.27:9090/')
culd = ServiceProxy('http://localhost:4339/')
apikey = 'AIzaSyBLk_iU8ORnHM39YQCUsHngMfG85Rg9yss'

newarrivallist = {}
newetalist = {}
achievments = {}

eventcache = []
eventdetailcache = []
eventcache_time = timezone.now() - timedelta(days=1)
event_details = []

artefactcache = {}
artefactcache_time = timezone.now() - timedelta(days=1)

hwstorage_state = "closed"

default_stripe_pattern = 4
default_stripe_speed = 3
default_stripe_offset = 0

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
    u = getuser(user)
    if u.logouttime + timedelta(seconds=hysterese) > timezone.now():
        return reply(request, "hysterese")
    else:
        welcometts(request, u.username)
        try:
            monitord.login(u.username)
        except:
            pass
        try: gcm_send(request, 'now boarding', user)
        except: pass
        if u.status == "eta":
            u.eta = ""
        u.status = "online"
        u.logintime=timezone.now()
        u.save()
        log_stats()
        newarrivallist[u.username] = timezone.now()
    return reply(request, "%s logged in" % u.username)

@jsonrpc_method('force_login')
def force_login(request, user):
    u = getuser(user)
    welcometts(request, u.username)
    try:
        monitord.login(u.username)
    except:
        pass
    try: gcm_send(request, 'now boarding', user)
    except: pass
    if u.status == "eta":
        u.eta = ""
    u.status = "online"
    u.logintime=timezone.now()
    u.save()
    log_stats()
    newarrivallist[u.username] = timezone.now()
    return reply(request, "%s logged in" % u.username)

@jsonrpc_method('stealth_login')
def stealth_login(request, user):
    u = getuser(user)
    if u.status == "eta":
        u.eta = ""
    u.status = "online"
    u.logintime=timezone.now()
    u.save()
    log_stats()
    newarrivallist[u.username] = timezone.now()
    return reply(request, "%s logged in" % u.username)


@jsonrpc_method('logout')
def logout(request, user):
    return stealth_logout(request, user)

@jsonrpc_method('stealth_logout')
def stealth_logout(request, user):
    u = getuser(user)
    if u.logintime + timedelta(seconds=hysterese) > timezone.now():
        return reply(request, "hysterese")
    else:
        try:
            monitord.logout(u.username)
        except:
            pass
        u.status = "offline"
        u.logouttime = timezone.now()
        u.save()
        log_stats()

    return reply(request, "%s logged out" % u.username)

@jsonrpc_method('force_logout')
def force_logout(request, user):
    u = getuser(user)
    try:
        monitord.logout(u.username)
    except:
        pass
    u.status = "offline"
    u.logouttime = timezone.now()
    u.save()
    log_stats()

    return reply(request, "%s logged out" % u.username)

#jsonrpc_method('login_wlan')
@jsonrpc_method('wifi_login')
def login_wlan(request, user):
    u = getuser(user)
    if is_logged_in(user):
        extend(user)
    else:
        if u.logouttime + timedelta(minutes=5) < timezone.now():
            login(request, user)
        else:
            print "hysterese"

def extend(user):
    print("extend %s" % user)
    u = getuser(user)
    u.status = "online"
    u.logintime=timezone.now()
    u.save()
    return "aye"

@jsonrpc_method('tagevent')
def tagevent(request, user):
    if is_logged_in(user): # TODO and logintimeout
        return logout(request, user)
    else:
        return login(request, user)

def welcometts(request, user):
    #if os.path.isfile('%s/%s/hello.mp3' % (cfg.sampledir, user)):
    #    os.system('mpg123 %s/%s/hello.mp3' % (cfg.sampledir, user))
    #else:
    if getnickspell(request, user) != "NONE":
        if user == "kristall":
            tts(request, "julia", "a loa crew")
        else:
            tts(request, "julia", cfg.ttsgreeting % getnickspell(request, user))

#################################################################
# User Handling
#################################################################

def getuser(user):
    if user == "nielc": user = "keiner"
    if user == "azt": user = "pille"
    try:
        u = User.objects.get(username=user)
    except:
        u = User(username=user, logintime=timezone.now()-timedelta(seconds=hysterese), logouttime=timezone.now()-timedelta(seconds=hysterese), status="unknown")
        u.save()
    return u


@jsonrpc_method('get_user_by_id')
def get_user_by_id(request, id):
    u = User.objects.get(id=id)
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
    eta = "0"

    # if the first argument is a weekday, delegate to LTE
    #TODO
    #if text[:2].upper() in weekdays:
        #return lte(bot, ievent)

    if text in ('gleich', 'bald', 'demnaechst', 'demnächst', 'demn\xe4chst'):
        etaval = datetime.datetime.now() + datetime.timedelta(minutes=30)
        eta = etaval.strftime("%H%M")
    elif text.startswith('+'):
        foo = int(text[1:])
        etaval = datetime.datetime.now() + datetime.timedelta(minutes=foo)
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

    tts(request, "julia", "E.T.A. %s: %d Uhr %d ." % (getnickspell(request, user), hour, minute))
    return seteta(request, user, eta)

@jsonrpc_method('seteta')
def seteta(request, user, eta):
    #data['newetas'][user] = eta
    u = getuser(user)

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

        #print etatimestamp
        u.eta = eta
        u.etatimestamp = etatimestamp
        u.status = "eta"
        u.save()
        try: gcm_send(request, 'ETA', '%s (%s)' % (user, eta))
        except: pass
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
    u = getuser(user)
    u.etasub = True
    u.save()

@jsonrpc_method('unsubeta')
def unsubeta(request, user):
    u = getuser(user)
    u.etasub = False
    u.save()

@jsonrpc_method('subarrive')
def subarrive(request, user):
    u = getuser(user)
    u.arrivesub = True
    u.save()

@jsonrpc_method('unsubarrive')
def unsubarrive(request, user):
    u = getuser(user)
    u.arrivesub = False
    u.save()

@jsonrpc_method('newetas')
def newetas(request):
    global newetalist
    tmp = newetalist
    newetalist = {}
    #if len(tmp) > 0:
    #    gcm_send(request, 'ETA', ', '.join(['%s (%s)' % (key, tmp[key]) for key in tmp.keys()]))
    #print "newetas_done"
    return tmp

@jsonrpc_method('arrivals')
def arrivals(request):
    global newarrivallist
    tmp = newarrivallist
    newarrivallist = {}
    #if len(tmp) > 0:
    #    try: gcm_send(request, 'now boarding', ', '.join(tmp.keys()))
    #    except: pass
    #print "arrivals_done"
    return tmp

@jsonrpc_method('achievements')
def achievements(request):
    global achievements
    tmp = achievements
    achievements = {}
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
        if u.autologout_in() < 0:
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

    return 0


#################################################################
# event methods
#################################################################

@jsonrpc_method('events')
def events(request):
    global eventcache
    update_event_cache()
    return eventcache

@jsonrpc_method('event_list')
def event_list(request):
    global eventdetailcache
    update_event_cache()
    return eventdetailcache

@jsonrpc_method('event_detail')
def event_detail(request, id):
    d = feedparser.parse('http://www.c-base.org/calender/phpicalendar/rss/rss2.0.php?cal=&cpath=&rssview=today')
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
    try:
        d = feedparser.parse('http://www.c-base.org/calender/phpicalendar/rss/rss2.0.php?cal=&cpath=&rssview=today')
    except:
        pass

    if d is not None:
        for entry in d['entries']:
            entryid = 42
            try:
                entryid = re.search(r'.*&uid=(.*)@google.com', entry['id']).group(1)
            except: pass
            title = re.search(r'.*: (.*)', entry['title']).group(1)
            end = re.search(r'(\d\d\d\d-\d\d-\d\d)T(\d\d:\d\d):(\d\d)', entry['ev_enddate']).group(2).replace(':', '')
            start = re.search(r'(\d\d\d\d-\d\d-\d\d)T(\d\d:\d\d):(\d\d)', entry['ev_startdate']).group(2).replace(':', '')
            title = title.replace("c   user", "c++ user")

            description = entry['summary_detail']['value']
            events.append('%s (%s-%s)' % (title, start, end))
            event_details.append({'id': entryid, 'title':title, 'start': start, 'end': end, 'description': description})
        eventcache = events
        eventdetailcache = event_details
        eventcache_time = timezone.now()

def event_list_web(request):
    return render_to_response('cbeamd/event_list.django', {'event_list': event_list(request)})

#################################################################
# scanner methods
#################################################################

@jsonrpc_method('monmessage')
def monmessage(request, message):
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
    return cout.tts(voice, text)

@jsonrpc_method('r2d2')
def r2d2(request, text):
    return cout.r2d2(text)

@jsonrpc_method('play')
def play(request, file):
    return cout.play(file)

@jsonrpc_method('setvolume')
def setvolume(request, volume):
    return cout.setvolume(volume)

@jsonrpc_method('getvolume')
def getvolume(request, volume):
    return cout.getvolume(volume)

@jsonrpc_method('voices')
def voices(request):
    return cout.voices()

@jsonrpc_method('sounds')
def sounds(request):
    return cout.sounds()

@jsonrpc_method('c_out')
def c_out(request):
    return cout.c_out()

@jsonrpc_method('announce')
def announce(request, text):
    return cout.announce(text)

@login_required
def c_out_web(request):
    return render_to_response('cbeamd/c_out.django', {'sound_list': sounds(request)['result']})

@login_required
def c_out_play_web(request, sound):
    result = play(request, sound)
    return render_to_response('cbeamd/c_out.django', {'sound_list': sounds(request)['result'], 'result': "sound wurde abgespielt"})



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
    #print "%s (%s) got %s" % (name, mac, ip)
    #if data['macmap'].has_key(mac):
        #user = data['macmap'][mac]
        #save()
        #if user in userlist():
            #print "%s already logged in" % user
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

# cbeam.r0ketSeen(result.group(1), sensor, result.group(2), result.group(3))
@jsonrpc_method('r0ketseen')
def r0ketseen(request, r0ketid, sensor, payload, signal):
    timestamp = 42
#    if r0ketid in data['r0ketids'].keys():
#        #data['r0ketmap'][r0ketid] = [sensor, payload, signal, timestamp]
#        print 'r0ket %s detected, logging in %s (%s)' % (r0ketid, data['r0ketids'][r0ketid], sensor)
#        user = data['r0ketids'][r0ketid]
#        data['lastlocation'][user] = sensor
#        result = login(user)
#    else:
#        print 'saw unknown r0ket: %s (%s)' % (r0ketid, sensor)
#    save()
#    return "aye"
#
#def getr0ketmap():
#    return data['r0ketmap']
#
#def registerr0ket(r0ketid, user):
#    data['r0ketids'][r0ketid] = user
#    save()
#    return "aye"
#
#def getr0ketuser(r0ketid):
#    return data['r0ketids'][r0ketid]

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

def index(request):
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
def user(request, user_id):
    u = get_object_or_404(User, pk=user_id)
    return render_to_response('cbeamd/user_detail.django', {'user': u})

@login_required
def user_online(request):
    user_list = User.objects.filter(status="online").order_by('username')
    return render_to_response('cbeamd/user_list.django', {'user_list': user_list, 'status': 'online'})

@login_required
def user_offline(request):
    user_list = User.objects.filter(status="offline").order_by('username')
    return render_to_response('cbeamd/user_list.django', {'user_list': user_list, 'status': 'offline'})

@login_required
def user_eta(request):
    user_list = User.objects.filter(status="eta").order_by('username')
    return render_to_response('cbeamd/user_list.django', {'user_list': user_list, 'status': 'eta'})

@login_required
def user_all(request):
    user_list = User.objects.all().order_by('username')
    return render_to_response('cbeamd/user_list.django', {'user_list': user_list, 'status': 'all'})

@jsonrpc_method('user_list')
def user_list(request):
    users = User.objects.all().order_by('username')
    return [user.dic() for user in users]

@login_required
def control(request):
    return render_to_response('cbeamd/control.django', {})

#################################################################
# Web Login / Logout
#################################################################

def auth_login( request ):
    redirect_to = request.REQUEST.get( 'next', '' ) or '/'
    if request.method == 'POST':
        form = LoginForm( request.POST )
        if form.is_valid():
            username = form.cleaned_data['username']
            password = form.cleaned_data['password']
            user = authenticate( username=username, password=password )
            if user is not None:
                if user.is_active:
                    login_auth( request, user )
                    return HttpResponseRedirect( redirect_to )
    else:
        form = LoginForm()
    return render_to_response( 'cbeamd/login.django', RequestContext( request,
        locals() ) )

def auth_logout( request ):
    redirect_to = request.REQUEST.get( 'next', '' ) or '/'
    logout_auth( request )
    return HttpResponseRedirect( redirect_to )

#################################################################
# mission handling
#################################################################

@jsonrpc_method('add_mission')
def add_mission(request, short_description):
    m = Mission(short_description=short_description)
    m.save()
    return "aye"

@jsonrpc_method('missions')
def missions(request):
    return [str(mission) for mission in Mission.objects.all()]

@jsonrpc_method('mission_detail')
def mission_detail(request, mission_id):
    mission = get_object_or_404(Mission, pk=mission_id)
    return mission.dic()
    #return render_to_response('cbeamd/mission_detail.django', {'mission': mission})

@jsonrpc_method('mission_assign')
def mission_assign(request, user, mission_id):
    u = getuser(user)
    m = Mission.objects.get(id=mission_id)
    if m.status == "open":
        m.assigned_to = u
        m.status = "assigned"
        m.save()
        return "success"
    return "mission not available"

@jsonrpc_method('mission_cancel')
def mission_cancel(request, user, mission_id):
    u = getuser(user)
    m = Mission.objects.get(id=mission_id)
    if m.assigned_to == u and m.status == "assigned":
        m.assigned_to = None
        m.status = "open"
        m.save()
        return "success"
    return "not assigned to user"

@jsonrpc_method('mission_complete')
def mission_complete(request, user, mission_id):
    u = getuser(user)
    m = Mission.objects.get(id=mission_id)
    if m.assigned_to == u and m.status == "assigned":
        u.ap = u.ap + m.ap
        u.save()
        m.assigned_to = None
        m.status = "completed"
        m.save()
        mlog = MissionLog()
        mlog.user = u
        mlog.mission = m
        mlog.save()
        return "success"
    return "failure"



@jsonrpc_method('mission_list')
def mission_list(request):
    if request.path.startswith('/rpc'):
        missions = Mission.objects.all()
        return [mission.dic() for mission in missions]
    else:
        mission_list = Mission.objects.all()
        return render_to_response('cbeamd/mission_list.django', {'mission_list': mission_list})

def edit_mission(request, object_id):
    if request.method == "POST":
        m = Mission.objects.get(pk=object_id)
        form = MissionForm(request.POST, instance=m)
        if form.is_valid():
            form.save()
            return HttpResponseRedirect('/missions/%s' % object_id)
    else:
        m = Mission.objects.get(id=object_id)
        form = MissionForm(instance=m)
    return render_to_response('cbeamd/mission_form.django', locals(), context_instance = RequestContext(request))

#################################################################
# Google Cloud Messaging
#################################################################

@jsonrpc_method('gcm_register')
def gcm_register(request, user, regid):
    #print regid
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
    subscriptions = Subscription.objects.all()
    regids = [subscription.regid for subscription in subscriptions]
    data = {'title': title, 'text': text}
    response = gcm.json_request(registration_ids=regids, data=data)
    return response

@jsonrpc_method('gcm_send_test')
def gcm_send_test(request, title, text):
    gcm = GCM(apikey)
    u = getuser("smile")
    subscriptions = Subscription.objects.filter(user=u)
    regids = [subscription.regid for subscription in subscriptions]
    data = {'title': title, 'text': text}
    response = gcm.json_request(registration_ids=regids, data=data)
    return response

@jsonrpc_method('test_enc')
def test_enc(request):
    gcm = GCM(apikey)
    encrypted_data = crypto.EncryptWithAES("fooderbar")
    u = getuser("smile")
    s = Subscription.objects.get(user=u)
    #print encrypted_data
    regids = [s.regid]
    data = {'title': "AES", 'text': encrypted_data}
    response = gcm.json_request(registration_ids=regids, data=data)
    return encrypted_data


@jsonrpc_method('smile', authenticated=True)
def smile(request):
    return "aye"

#################################################################
# CULd method forwarding
#################################################################

@jsonrpc_method('bluewall()')#, authenticated=True, validate=True)
def bluewall(request):
    return culd.bluewall(True)

@jsonrpc_method('darkwall()')#, authenticated=True, validate=True)
def darkwall(REQUEST):
    return culd.bluewall(False)

#@jsonrpc_method('hwstorage(Boolean)', authenticated=True, validate=True)
@jsonrpc_method('hwstorage(bool)')
def hwstorage(request, status):
    global timer
    #global hwstorage_state
    #if hwstorage_state == "open":
        #return
    #hwstorage_state = "open"
    culd.hwstorage(True)
    culd.hwstorage(True)
    def close():
        culd.hwstorage(False)
        culd.hwstorage(False)
        #hwstorage_state = "closed"
    timer = Timer(30.0, close)
    timer.start()
    return "aye"

def hwstorage_web(request):
    result = hwstorage(request, True)
    return render_to_response('cbeamd/control.django', {'result': 'Software-Endlager wurde geöffnet: %s' % result})

#################################################################
# artefact handling
#################################################################

@jsonrpc_method('artefact_list')
def artefact_list(request):
    global artefactcache
    global artefactcache_time
    artefactlist = {}
    if artefactcache_time + timedelta(hours=1) < timezone.now():
        parser = MyHTMLParser()
        parser.feed(urlopen("http://cbag3.c-base.org/artefact/").read())
        artefacts = parser.get_artefacts()
        artefactlist = [{'name': key, 'slug': artefacts[key]} for key in artefacts.keys()]
        artefactcache = artefactlist
        artefactcache_time = timezone.now()
    else:
        artefactlist = artefactcache
    return sorted(artefactlist)

def artefact_list_web(request):
    return render_to_response('cbeamd/artefact_list.django', {'artefact_list': artefact_list(request)})

#################################################################
# article handling
#################################################################

@jsonrpc_method('list_articles')
def list_articles(request):
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
    return str(UserStatsEntry.objects.all())


#################################################################
# cerebrum leds methods
#################################################################

@jsonrpc_method('set_stripe_pattern')
def set_stripe_pattern(request, pattern_id):
    return cerebrum.set_pattern(pattern_id)

def set_stripe_pattern_web(request, pattern_id):
    print cerebrum.set_pattern(int(pattern_id))
    return render_to_response('cbeamd/control.django', {'result': 'Pattern wurde gesetzt'})

@jsonrpc_method('set_stripe_speed')
def set_stripe_speed(request, speed):
    return cerebrum.set_speed(speed)

def set_stripe_speed_web(request, speed):
    cerebrum.set_speed(int(speed))
    return render_to_response('cbeamd/control.django', {'result': 'Geschwindigkeit wurde gesetzt'})

@jsonrpc_method('set_stripe_offset')
def set_stripe_pattern(request, offset):
    return cerebrum.set_offset(offset)

@jsonrpc_method('set_stripe_buffer')
def set_stripe_buffer(request, buffer):
    #buffer = [255,0,0,255,0,0,255,0,0,255,0,0,0,255,0,0,255,0,0,255,0,0,255,0,0,0,255,0,0,255,0,0,255,0,0,255,0,0,0,0,0,0,0,0,0,0,0,0]*32+[0,0,0,0,0,0,0,0,0,0,0,0]
    #print buffer
    return cerebrum.set_buffer(buffer)

@jsonrpc_method('set_stripe_default')
def set_stripe_default(request):
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
    global default_stripe_pattern
    global default_stripe_speed
    default_stripe_pattern = 10
    default_stripe_speed = 0
    cerebrum.set_pattern(10)
    cerebrum.set_speed(1)

@jsonrpc_method('rainbow')
def rainbow(request):
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
    now = DDate()
    now.fromDate(date.today())
    return "Today is "+str(now)

@jsonrpc_method('fnord')
def fnord(request):
    return DDate().fnord()


@jsonrpc_method('isWifiLoginEnabled()')
def isWifiLoginEnabled(request, users):
    #print users
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
            #print form
            return render_to_response('cbeamd/stripe_form.django', {'form': form})
    else:
        form = StripeForm()
        return render_to_response('cbeamd/stripe_form.django', {'form': form})
