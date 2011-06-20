
import jsonrpclib
import sys
import os
import datetime

jsonrpclib.config.version = 1.0
server = jsonrpclib.Server('http://10.0.1.13:1775')

userdir = "/home/c-beam/users"

logindelta = 10


def tts(voice, text):
    print server.tts(voice, text)


def log(message):
    print "%s: %s" % (datetime.datetime.now(),message)

def login(user, timeoutdelta):
    log("called login for %s" % user)
    if user == "unknown":
        return "login"
    userfile = '%s/%s' % (userdir, user)
    if os.path.isfile(userfile):
        timestamps = eval(open(userfile).read())
        now = int(datetime.datetime.now().strftime("%Y%m%d%H%M%S"))
        if timestamps[0] - now > 0:
           # multiple logins, ignore
           log("multiple logins, ignoring")
           return "ignore"
        else:
           #logout
           log("%s logged out" % user)
           os.rename(userfile, "%s.logout" % userfile)
           return "logout"
    else:
        if os.path.isfile("%s.logout" % userfile):
           return "ignore"
        else:
           logints = datetime.datetime.now() + datetime.timedelta(seconds=logindelta)
           timeoutts = datetime.datetime.now() + datetime.timedelta(minutes=timeoutdelta)
           expire = [int(logints.strftime("%Y%m%d%H%M%S")), int(timeoutts.strftime("%Y%m%d%H%M%S"))]
           f = open(userfile, 'w')
           f.write(str(expire))
           log("%s logged in" % user)
           return "login"
