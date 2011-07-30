#! /usr/bin/python
# -*- coding: utf-8 -*-

import httplib, urllib, random, re, os, sys, time, subprocess
import logging
import datetime
import stat

from jsonrpclib.SimpleJSONRPCServer import SimpleJSONRPCServer

#jsonrpclib.config.version = 1.0
#server = jsonrpclib.Server('http://10.0.1.13:1775')

userdir = "/home/c-beam/users"

logindelta = 30

logfile = '/home/smile/c-beam.log'

logger = logging.getLogger('c-beam')
hdlr = logging.FileHandler(logfile)
formatter = logging.Formatter('%(asctime)s %(levelname)s %(message)s')
hdlr.setFormatter(formatter)
logger.addHandler(hdlr) 
logger.setLevel(logging.INFO)

timeoutdelta = 600

def main():

    server = SimpleJSONRPCServer(('0.0.0.0', 4254))

    server.register_function(logout, 'logout')
    server.register_function(login, 'login')
    server.register_function(tagevent, 'tagevent')
    #server.register_function(eta, 'eta')
    server.serve_forever()

def login(user):
    userfile = '%s/%s' % (userdir, user)
    logints = datetime.datetime.now() + datetime.timedelta(seconds=logindelta)
    timeoutts = datetime.datetime.now() + datetime.timedelta(minutes=timeoutdelta)
    expire = [int(logints.strftime("%Y%m%d%H%M%S")), int(timeoutts.strftime("%Y%m%d%H%M%S"))]
    f = open(userfile, 'w')
    f.write(str(expire))
    #os.chown(userfile, 11488, 11489)
    os.chmod(userfile, stat.S_IREAD|stat.S_IWRITE|stat.S_IRGRP|stat.S_IWGRP)
    return "aye"

def logout(user):
    userfile = '%s/%s' % (userdir, user)
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

if __name__ == "__main__":
    main()

