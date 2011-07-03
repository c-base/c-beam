# -*- coding: utf-8 -*-
# jsb.plugs.common/c_out.py
#
#

""" text to speech. """

## jsb imports

from jsb.utils.exception import handle_exception
from jsb.lib.commands import cmnds
from jsb.lib.examples import examples
from jsb.lib.persistconfig import PersistConfig
from jsb.lib.persist import PlugPersist

## basic imports

import re
import random
import os
import urllib
import sys
import jsonrpclib
import datetime

## defines


cfg = PersistConfig()
cfg.define('rpcurl', 'http://10.0.1.13:1775')

usermap = eval(open('%s/usermap' % cfg.get('datadir')).read())
c_outlog = '%s/botlogs/c_out.log' % cfg.get('datadir')

jsonrpclib.config.version = 1.0
server = jsonrpclib.Server(cfg.get('rpcurl'))

def getuser(ievent):
    if ievent.channel in usermap:
        return usermap[ievent.channel]
    elif ievent.fromm and ievent.fromm in usermap:
        return usermap[ievent.fromm]
    elif ievent.nick and ievent.nick in usermap:
        return usermap[ievent.nick]
    elif ievent.ruserhost in usermap:
        return usermap[ievent.ruserhost]
    elif ievent.channel.find('c-base.org') > -1:
        return ievent.channel[:-11]
    elif ievent.fromm and ievent.fromm.find('c-base.org') > -1:
        return ievent.fromm[:-10]
    elif ievent.hostname.startswith('c-base/crew/'):
        return ievent.hostname[12:]
    elif ievent.hostname.startswith('pdpc/supporter/professional/'):
        return ievent.hostname[28:]
    elif ievent.auth.endswith('@shell.c-base.org'):
        return ievent.auth[1:-17]
    else:
        return 0

## c_out command

def handle_c_out(bot, ievent):
    """ text to speech synthesis. """
    if not ievent.args:
        sound = random.choice(server.sounds())
    else:
        sound = ievent.rest
    try:
        ievent.reply(server.play(sound))
        #f = open(c_outlog, 'a')
        #f.write('%s: %s: %s (%s)\n' % (datetime.datetime.now(), getuser(ievent), sound))
        #f.close()
    except:
        ievent.reply(str(sys.exc_info()[0]))

cmnds.add('c_out', handle_c_out, ['USER', 'GUEST'])

def handle_c_out_list(bot, ievent):
    return ievent.reply(" ".join(server.sounds()))

cmnds.add('c_out-list', handle_c_out_list, ['USER', 'GUEST'])

def tail(f, n, offset=0):
    """Reads a n lines from f with an offset of offset lines."""
    avg_line_length = 74
    to_read = n + offset
    while 1:
        try:
            f.seek(-(avg_line_length * to_read), 2)
        except IOError:
            # woops.  apparently file is smaller than what we want
            # to step back, go to the beginning instead
            f.seek(0)
        pos = f.tell()
        lines = f.read().splitlines()
        if len(lines) >= to_read or pos == 0:
            return lines[-to_read:offset and -offset or None]
        avg_line_length *= 1.3

def handle_c_out_tail(bot, ievent):
    print "tail"
    f = open(c_outlog)
    ievent.reply('\n'.join(tail(f, 5, 0)))
    f.close()

cmnds.add('c_out-tail', handle_c_out_tail, ['USER', 'GUEST'])
