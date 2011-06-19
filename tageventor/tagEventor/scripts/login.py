
import jsonrpclib
import sys
import os
import datetime

jsonrpclib.config.version = 1.0
server = jsonrpclib.Server('http://10.0.1.13:1775')

userdir = "/home/c-beam/users"


def tts(voice, text):
    print server.tts(voice, text)


def login(user, logindelta, timeoutdelta):
    if user == "unknown":
        return "login"
    userfile = '%s/%s' % (userdir, user)
    if os.path.isfile(userfile):
        print userfile
        timestamps = eval(open(userfile).read())
        print timestamps
        now = int(datetime.datetime.now().strftime("%Y%m%d%H%M%S"))
        if timestamps[0] - now > 0:
           # multiple logins, ignore
           print "multiple logins, ignoring"
           return "ignore"
        else:
           #logout
           os.rename(userfile, "%s.logout" % userfile)
           return "logout"
    else:
        if os.path.isfile("%s.logout" % userfile):
           return "ignore"
        else:
           logints = datetime.datetime.now() + datetime.timedelta(minutes=logindelta)
           timeoutts = datetime.datetime.now() + datetime.timedelta(minutes=timeoutdelta)
           #eta = int(foo.strftime("%Y%m%s%H%M"))
           expire = [int(logints.strftime("%Y%m%d%H%M%S")), int(timeoutts.strftime("%Y%m%d%H%M%S"))]
           print expire
           f = open(userfile, 'w')
           f.write(str(expire))

           return "login"
