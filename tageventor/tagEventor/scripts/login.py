
import jsonrpclib
import sys
import os
import datetime
import stat

jsonrpclib.config.version = 1.0
server = jsonrpclib.Server('http://10.0.1.27:4254/rpc/')

userdir = "/home/c-beam/users"

logindelta = 30


def tts(voice, text):
    print server.tts(voice, text)


def log(message):
    print "%s: %s" % (datetime.datetime.now(),message)

def login(user, timeoutdelta):
    log("called login for %s" % user)

    return server.tagevent(user)

def unknowntag(rfid):
    return server.unknown_tag(rfid)
