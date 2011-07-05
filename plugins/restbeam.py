# myplugs/restbeam.py
#
#

## gozerbot imports

from jsb.lib.persist import PlugPersist, Persist
from jsb.lib.commands import cmnds
from jsb.lib.persistconfig import PersistConfig
#from jsb.lib.socklib.rest.server import RestServer, RestRequestHandler
from jsb.lib.rest.server import RestServer, RestRequestHandler
from jsb.utils.exception import handle_exception
from jsb.utils.textutils import html_unescape
from jsb.lib.datadir import getdatadir
from jsb.imports import getjson

from jsb.lib.callbacks import callbacks
from jsb.utils.url import posturl, getpostdata
from jsb.lib.persistconfig import PersistConfig
from jsb.lib.commands import cmnds
from jsb.lib.eventbase import EventBase
from jsb.utils.exception import handle_exception
from jsb.lib.examples import examples

## basic imports

import socket
import re
import logging
import os
import time

## VARS

cfg = PersistConfig()
cfg.define('enable', 0)
cfg.define('host' , socket.gethostbyname(socket.getfqdn()))
cfg.define('name' , socket.getfqdn())
cfg.define('port' , 10102)
cfg.define('disable', [])

hp = "%s:%s" % (cfg.get('host'), cfg.get('port'))
url = "http://%s" % hp

usermap = '/home/c-beam/usermap'
scriptdir = '/home/smile/projects/c-beam/tageventor/tagEventor/scripts'
userpath = '/home/c-beam/users'
logfile = '/var/log/c-beam/c-beamhttp.log'
logindelta = 30
timeoutdelta = 600

## callbacks

## server part

server = None

def getuserbyuuid(uuid):
    userfile = '%s/%s' % (usermap, uuid)
    if os.path.exists(userfile) and os.path.isfile(userfile):
        f = open(userfile, "r")
        username = f.read()
        username = username.rstrip('\n')
        f.close()
        return username
    else:
        return 0

def home_GET(server, request):
    try:
        return "willcommen auf der c-beam REST API."
    except Exception, ex:
        handle_exception()


def topstats_GET(server, request):
    try:
        return "Hallo Welt: topstats_GET"
    except Exception, ex:
        handle_exception()

def playlist_GET(server, request):
    try:
        return "playlist_GET: %s" % request
    except Exception, ex:
        handle_exception()

def login_GET(server, request):
    uuid = 42 #request.get
    username = getuserbyuuid(uuid)
    if username == 0:
        return "ERR"
    userloginfile = '%s/%s' % (userpath, username)
    logints = datetime.datetime.now() + datetime.timedelta(seconds=logindelta)
    timeoutts = datetime.datetime.now() + datetime.timedelta(minutes=timeoutdelta)
    expire = [int(logints.strftime("%Y%m%d%H%M%S")), int(timeoutts.strftime("%Y%m%d%H%M%S"))]
    f = open(userloginfile, 'w')
    f.write(str(expire))
    f.close()
    return '<h1>hallo %s, willkommen auf der c-base.</h1>' % username


def logout_GET(server, request):
    if os.path.exists('%s/%s' % (userpath, username)):
        os.remove('%s/%s' % (userpath, username))
    return 'danke, daC du dich abgemeldet hast.'


def startserver():
    global server 
    try:
        logging.warn('restbeam - starting server at %s:%s' % (cfg.get('host'), cfg.get('port')))
        time.sleep(2)
        server = RestServer((cfg.get('host'), cfg.get('port')), RestRequestHandler)

        if server:
            server.start()
            logging.warn('restbeam - running at %s' % url)
            server.addhandler('/', 'GET', playlist_GET)
            server.addhandler('/login/*', 'GET', login_GET)
            server.addhandler('/logout/', 'GET', logout_GET)
            server.addhandler('/top/', 'GET', topstats_GET)
            server.addhandler('/top', 'GET', topstats_GET)
            for mount in cfg.get('disable'): server.disable(mount)
        else: logging.error('restbeam - failed to start server at %s:%s' % (cfg.get('host'), cfg.get('port')))

    except socket.error, ex: logging.warn('restbeam - server - %s' % str(ex))
    except Exception, ex: handle_exception()

def stopserver():
    try:
        if not server: logging.warn('restbeam - server is already stopped') ; return
        server.shutdown()
        time.sleep(3)
    except Exception, ex: handle_exception()

## plugin init

def init():
    if cfg['enable']: startserver()

def shutdown():
    if cfg['enable']: stopserver()

def handle_restbeam_start(bot, event):
    cfg['enable'] = 1
    cfg.save()
    startserver()
    event.done()

cmnds.add('restbeam-start', handle_restbeam_start, 'OPER')

def handle_restbeam_stop(bot, event):
    cfg['enable'] = 0
    cfg.save()
    stopserver()
    event.done()

cmnds.add('restbeam-stop', handle_restbeam_stop, 'OPER')
