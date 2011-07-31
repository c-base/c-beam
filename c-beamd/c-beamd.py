#! /usr/bin/python
# -*- coding: utf-8 -*-

import httplib, urllib, random, re, os, sys, time, subprocess
import logging
import datetime
import stat

from jsonrpclib.SimpleJSONRPCServer import SimpleJSONRPCServer

import jsonrpclib

jsonrpclib.config.version = 1.0
c_out = jsonrpclib.Server('http://10.0.1.13:1775')

userdir = "/home/c-beam/users"
datafile = "/home/c-beam/c-beam.data"

logindelta = 30

logfile = '/home/smile/c-beam.log'

nickspells = {}

data = {
    'etas': {},
    'etds': {},
    'etatimestamps': {},
    'etdtimestamps': {}
}

eta_timeout = 120
etd_timeout = 120

logger = logging.getLogger('c-beam')
hdlr = logging.FileHandler(logfile)
formatter = logging.Formatter('%(asctime)s %(levelname)s %(message)s')
hdlr.setFormatter(formatter)
logger.addHandler(hdlr) 
logger.setLevel(logging.INFO)

timeoutdelta = 600

def init():
    global nickspells
    global data
    try:
        nickspells = eval(open('nickspell').read())
        data = eval(open(datafile).read())
        print nickspells
        print data
    except: pass
    return 0

def main():
    init()
    server = SimpleJSONRPCServer(('0.0.0.0', 4254))

    server.register_function(logout, 'logout')
    server.register_function(login, 'login')
    server.register_function(tagevent, 'tagevent')
    server.register_function(eta, 'eta')
    server.register_function(etd, 'etd')
    server.register_function(who, 'who')
    server.register_function(geteta, 'geteta')
    server.register_function(getetd, 'getetd')
    server.register_function(available, 'available')
    server.register_function(getnickspell, 'getnickspell')
    server.register_function(setnickspell, 'setnickspell')
    
    server.serve_forever()

def getnickspell(user):
    if user in nickspells.keys():
        return nickspells[user]
    else:
        return user

def setnickspell(user, nickspell):
    print nickspell
    nickspells[user] = nickspell
    f = open('nickspell', 'w')
    f.write(str(nickspells))
    f.close()
    return "ok"

def login(user):
    userfile = '%s/%s' % (userdir, user)
    logints = datetime.datetime.now() + datetime.timedelta(seconds=logindelta)
    timeoutts = datetime.datetime.now() + datetime.timedelta(minutes=timeoutdelta)
    expire = [int(logints.strftime("%Y%m%d%H%M%S")), int(timeoutts.strftime("%Y%m%d%H%M%S"))]
    f = open(userfile, 'w')
    f.write(str(expire))
    #os.chown(userfile, 11488, 11489)
    os.chmod(userfile, stat.S_IREAD|stat.S_IWRITE|stat.S_IRGRP|stat.S_IWGRP)
    c_out.tts("julia", "hallo %s, willkommen an bord" % getnickspell(user))
    return "aye"

def logout(user):
    userfile = '%s/%s' % (userdir, user)
    c_out.tts("julia", "guten heimflug %s." % getnickspell(user))
    os.rename(userfile, "%s.logout" % userfile)
    return "aye"

def log(message):
    print "%s: %s" % (datetime.datetime.now(),message)

def tagevent(user):
    log("called tagevent for %s" % user)
    if user == "unknown":
        return "login"
    userfile = '%s/%s' % (userdir, user)
    if os.path.isfile(userfile):
        timestamps = eval(open(userfile).read())
        now = int(datetime.datetime.now().strftime("%Y%m%d%H%M%S"))
        if timestamps[0] - now > 0:
           # multiple logins, ignore
           log("multiple logins from %s, ignoring" % user)
           return "ignore"
        else:
           #logout
           return logout(user)
           log("%s logged out" % user)
           return "logout"
    else:
        if os.path.isfile("%s.logout" % userfile):
           return "ignore"
        else:
           log("%s logged in" % user)
           return login(user)

def seteta(user, eta):
    if eta == '0':
        if data['etas'].has_key(user):
            del data['etas'][user]
    else:
        arrival = extract_eta(eta)

        arrival_hour = int(arrival[0:2]) % 24
        arrival_minute = int(arrival[3:4]) % 60
         
#        arrival = str((int(arrival) + delta) % 2400)
        etatimestamp = datetime.datetime.now().replace(hour=arrival_hour, minute=arrival_minute) + datetime.timedelta(minutes=eta_timeout)
        if datetime.datetime.now().strftime("%H%M") > arrival: 
            etatimestamp = etatimestamp + datetime.timedelta(days=1)
        data['etas'][user] = eta
        data['etatimestamps'][user] = int(etatimestamp.strftime("%Y%m%d%H%M%S"))
    return "aye"

def save():
    f = open(datafile, 'w')
    f.write(str(data))
    f.close()

def extract_eta(text):
    m = re.match(r'^.*?(\d\d\d\d).*', text)
    if m:
        return m.group(1)
    else:
        return "9999"

def eta(user, text):
    eta = "0"

    # if the first argument is a weekday, delegate to LTE
    #if args[0].upper() in weekdays:
    #    return handle_lte(bot, ievent)

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
        return ['err_timeparser']

    return seteta(user, eta)

    if eta == "0":
        return ['eta_removed', user, str(eta)]
    else:
        return ['eta_set', user, eta]


def userlist():
    users = sorted(os.listdir(userdir))
    for user in users:
        if user.endswith(".logout"):
            users.remove(user)
    return users


def available():
    return userlist()

def who():
    """list all user that have logged in on the mirror."""
    return {'available': userlist(), 'eta': data['etas'], 'etd': data['etds']}

def login_tocen(bot, ievent):
    tocendir = cfg.get('tocendir')
    user = getuser(ievent)
    if not user: return ievent.reply(getmessage('unknown_nick'))
    presencename = 'presence.c-base.org/%s' % user
    userid = uuid.uuid3(uuid.NAMESPACE_DNS, presencename.encode('utf8')).hex
    tocenfile = '%s/%s' % (tocendir, userid)
    if not os.path.exists(tocenfile):
       f = open('%s/%s' % (tocendir, userid), 'w')
       f.write(user)
       f.close()
    httpurl = "http://10.0.1.27:8080"
    return ievent.reply('%s/login/%s' % (httpurl, userid))


def setetd(user, etd):
    if etd == '0':
        if data['etds'].has_key(user):
            del data['etds'][user]
    else:
        arrival = extract_eta(etd)

        arrival_hour = int(arrival[0:2]) % 24
        arrival_minute = int(arrival[3:4]) % 60
         
#        arrival = str((int(arrival) + delta) % 2400)
        etdtimestamp = datetime.datetime.now().replace(hour=arrival_hour, minute=arrival_minute) + datetime.timedelta(minutes=etd_timeout)
        if datetime.datetime.now().strftime("%H%M") > arrival: 
            etdtimestamp = etdtimestamp + datetime.timedelta(days=1)
        
        data['etds'][user] = etd
        data['etdtimestamps'][user] = int(etdtimestamp.strftime("%Y%m%d%H%M%S"))
    save()

def etd(user, etdtext):
    # return userlist if no arguments are provided
    if etdtext in ('gleich', 'bald', 'demnaechst', 'demnächst', 'demn\xe4chst'):
        etdval = datetime.datetime.now() + datetime.timedelta(minutes=30)
        etd = etdval.strftime("%H%M")
    elif etdtext.startswith('+'):
        foo = int(etdtext[0][1:])
        etdval = datetime.datetime.now() + datetime.timedelta(minutes=foo)
        etd = etdval.strftime("%H%M")
    elif etdtext == 'heute nicht mehr':
        etd = "0"
    else:
        etd = etdtext

    # remove superflous colons
    etd = re.sub(r'(\d\d):(\d\d)',r'\1\2',etd)
    #etd = re.sub(r'(\d\d).(\d\d)',r'\1\2',etd)

    if etd != "0" and extract_eta(etd) == "9999":
        return 'err_timeparser'



    logging.info("ETA: %s" % etd)
    setetd(user, etd)

    if etd == "0":
        return 'etd_removed'
    else:
        return 'etd_set'
 
def settimeout(user, timeout):
    data['logintimeouts'][user] = timeout
    save()


def geteta():
    return data['etas']

def getetd():
    return data['etds']



if __name__ == "__main__":
    main()

