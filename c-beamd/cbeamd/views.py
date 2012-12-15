from jsonrpc import jsonrpc_method
from models import User
from datetime import datetime, timedelta
from django.utils import timezone
from jsonrpc.proxy import ServiceProxy
#from django.conf import settings
import cbeamdcfg as cfg

import os, re, feedparser

hysterese = 3
eta_timeout=120

cout = ServiceProxy('http://10.0.1.13:1775/')
monitord = ServiceProxy('http://10.0.1.27:9090/')

newarrivallist = []
newetalist = []

#@jsonrpc_method('who')
#def who(request):
    #available = User.objects.filter(status="online")
    #if len(available) < 1:
        #return "niemand da"
    #else:
        #return "an bord [%s]: " % len(available) + ", ".join([str(a) for a in available])

@jsonrpc_method('login')
def login(request, user):
    if user == "nielc": user = "keiner"
    if user == "azt": user = "pille"
    u = getuser(user)
    if u.logouttime + timedelta(seconds=hysterese) > timezone.now():
        return "hysterese"
    else:
        #if u.status != "online":
        welcometts(request, user)
        monitord.login(user)
        if u.status == "eta":
            #remove eta
            u.eta = ""
        u.status = "online"
        u.logintime=timezone.now()
        u.save()
        newarrivallist.append(user)
    return "%s logged in" % user

@jsonrpc_method('logout')
def logout(request, user):
    if user == "nielc": user = "keiner"
    if user == "azt": user = "pille"
    u = getuser(user)
    if u.logintime + timedelta(seconds=hysterese) > timezone.now():
        return "hysterese"
    else:
        monitord.logout(user)
        u.status = "offline"
        u.logouttime = timezone.now()
        u.save()

    return "%s logged out" % user

@jsonrpc_method('getnickspell')
def getnickspell(request, user):
    u = getuser(user)
    if u.nickspell == None:
        return user
    else:
        return u.nickspell

@jsonrpc_method('setnickspell')
def setnickspell(request, user, nickspell):
    nickspells[user] = nickspell
    #f = open('nickspell', 'w')
    #f.write(str(nickspells))
    #f.close()
    return "ok"

def is_logged_in(user):
    return len(User.objects.filter(username=user, status="online")) > 0
    
@jsonrpc_method('login_wlan')
def login_wlan(request, user):
    if user == "nielc": user = "keiner"
    if user == "azt": user = "pille"

    logger.info("login_wlan(%s)" % user)
    if is_logged_in(user):
        logger.info("login_wlan(%s): already logged in" % user)
        extend(user)
    else:
        now = int(datetime.now().strftime("%Y%m%d%H%M%S"))
        if now - data['lastlogout'][user] > 300:
            login(user)

def welcometts(request, user):
    #if os.path.isfile('%s/%s/hello.mp3' % (cfg.sampledir, user)):
    #    os.system('mpg123 %s/%s/hello.mp3' % (cfg.sampledir, user))
    #else:
    if getnickspell(request, user) != "NONE":
        if user == "kristall":
            tts(request, "julia", "a loa crew")
        else:
            tts(request, "julia", cfg.ttsgreeting % getnickspell(request, user))

def getuser(user):
    try:
        u = User.objects.get(username=user)
    except:
        u = User(username=user, logintime=timezone.now(), logouttime=timezone.now(), status="unknown")
        u.save()
    return u

@jsonrpc_method('tagevent')
def tagevent(request, user):
    if user == "nielc": user = "keiner"
    if user == "azt": user = "pille"
    if is_logged_in(user): # TODO and logintimeout
        return logout(request, user)
    else:
        return login(request, user)

@jsonrpc_method('seteta')
def seteta(request, user, eta):
    #data['newetas'][user] = eta
    u = getuser(user)

    newetalist.append("%s (%s)" % (u.username, u.eta))
    if eta == '0':
        # delete eta for user
        u.eta=""
        u.status = "offline"
        u.save()
        return 'eta_removed'
    else:
        arrival = extract_eta(eta)

        arrival_hour = int(arrival[0:2]) % 24
        arrival_minute = int(arrival[3:4]) % 60

        etatimestamp = timezone.now().replace(hour=arrival_hour, minute=arrival_minute) + timedelta(minutes=eta_timeout)

        if timezone.now().strftime("%H%M") > arrival:
            etatimestamp = etatimestamp + timedelta(days=1)

        print etatimestamp
        u.eta = eta
        u.etatimestamp = etatimestamp
        u.status = "eta"
        u.save()
        return 'ETA has been set.'
def extract_eta(text):
    m = re.match(r'^.*?(\d\d\d\d).*', text)
    if m:
        return m.group(1)
    else:
        return "9999"

@jsonrpc_method('cleanup')
def cleanup(request):
    users = userlist()
    usercount = len(users)

    now = int(timezone.now().strftime("%Y%m%d%H%M%S"))

    # remove expired users
    for u in User.objects.filter(status="online"):
        if u.logintime + timedelta(minutes=cfg.timeoutdelta) < timezone.now():
            u.status="offline"
            u.logouttime = timezone.now()
            u.save()

    # remove expired ETAs
    for u in User.objects.filter(status="eta"):
        if u.etatimestamp < timezone.now():
            u.eta=""
            u.save()

    # remove expired ETDs
    return 0

def userlist():
    return [str(user) for user in User.objects.filter(status="online")]

@jsonrpc_method('available')
def available(request):
    cleanup(request)
    return userlist()

def ceitloch():
    now = int(timezone.now().strftime("%Y%m%d%H%M%S"))
    cl = {}
    for user in User.objects.filter(status="online"):
        td = timezone.now() - user.logintime
        cl[str(user)] = str(td.seconds)
    return cl

def reminder():
    result = {}
    for u in User.objects.filter(status="eta"):
        result[u.username] = u.reminder
    return result

def etalist():
    result = {}
    for u in User.objects.filter(status="eta"):
        result[u.username] = u.eta
    return result

@jsonrpc_method('who')
def who(request):
    """list all user that have logged in."""
    cleanup(request)
    return {'available': userlist(), 'eta': etalist(), 'etd': [], 'lastlocation': {}, 
            'ceitloch': ceitloch(), 'reminder': reminder()}

@jsonrpc_method('newetas')
def newetas(request):
    global newetalist
    tmp = newetalist
    newetalist = []
    return tmp

@jsonrpc_method('arrivals')
def arrivals(request):
    global newarrivallist
    tmp = newarrivallist
    newarrivallist = []
    return tmp

#################################################################
# misc methods
#################################################################

@jsonrpc_method('setdigitalmeter')
def setdigitalmeter(request, meterid, value):
    os.system('curl -d \'{"method":"set_digital_meter","id":0,"params":[%d,"%s"]}\' http://altar.cbrp3.c-base.org:4568/jsonrpc' % (meterid, value))
    return "aye"

@jsonrpc_method('events')
def events(request):
    events = []
    d = feedparser.parse('http://www.c-base.org/calender/phpicalendar/rss/rss2.0.php?cal=&cpath=&rssview=today')
    for entry in d['entries']:
        title = re.search(r'.*: (.*)', entry['title']).group(1)
        end = re.search(r'(\d\d\d\d-\d\d-\d\d)T(\d\d:\d\d):(\d\d)', entry['ev_enddate']).group(2).replace(':', '')
        start = re.search(r'(\d\d\d\d-\d\d-\d\d)T(\d\d:\d\d):(\d\d)', entry['ev_startdate']).group(2).replace(':', '')
        title = title.replace("c   user", "c++ user")
        events.append('%s (%s-%s)' % (title, start, end))
    return events

@jsonrpc_method('monmessage')
def monmessage(request, message):
    monitord.message(message)
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
    #if r0ketid in data['r0ketids'].keys():
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
