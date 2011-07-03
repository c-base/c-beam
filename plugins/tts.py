# -*- coding: utf-8 -*-
# jsb.plugs.common/tts.py
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
cfg.define('local', False)

usermap = eval(open('%s/usermap' % cfg.get('datadir')).read())
ttsdata = eval(open('%s/ttsdata' % cfg.get('datadir')).read())
ttslog = '%s/botlogs/tts.log' % cfg.get('datadir')

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
        return '%s - %s' % (ievent.nick, ievent.ruserhost)

## tts command

def handle_tts(bot, ievent, voice):
    """ text to speech synthesis. """
    if not ievent.args:
        #ievent.missing('<text>')
        #return
        text = random.choice(ttsdata.values()).encode("utf-8")
    else:
        text = ievent.rest.encode("utf-8")

    text = text.lower()

    text = text.replace('$','Dollar')
    if (voice in ['julia', 'sarah', 'klaus']):
        text = text.replace('c-base','zieh baejs')
        text = text.replace('c-beam','zieh biem')
        text = text.replace('c3pb', 'zeh drei p b')
    
    try:
        if cfg.get('local'):
            #os.system("echo %s | festival --tts" % ievent.rest)
            os.system("tts.py %s %s | xargs mpg123" % (voice, urllib.quote(text)))
        else:
            ievent.reply(server.tts(voice, urllib.quote(text)))
             
    except:
        ievent.reply(str(sys.exc_info()[0]))
    try:
        f = open(ttslog, 'a')
        f.write('%s: %s: %s (%s)\n' % (datetime.datetime.now(), getuser(ievent), text, voice))
        f.close()
    except:
        ievent.reply(str(sys.exc_info()[0]))

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

def handle_tts_tail(bot, ievent):
    print "tail"
    f = open(ttslog)
    ievent.reply('\n'.join(tail(f, 5, 0)))
    f.close()

handle_tts_default = lambda b,i: handle_tts(b,i,'julia')
handle_tts_julia = lambda b,i: handle_tts(b,i,'julia')
handle_tts_sarah = lambda b,i: handle_tts(b,i,'sarah')
handle_tts_klaus = lambda b,i: handle_tts(b,i,'klaus')
handle_tts_de = lambda b,i: handle_tts(b,i,'de')
handle_tts_lucy = lambda b,i: handle_tts(b,i,'lucy')
handle_tts_peter = lambda b,i: handle_tts(b,i,'peter')
handle_tts_rachel = lambda b,i: handle_tts(b,i,'rachel')
handle_tts_heather = lambda b,i: handle_tts(b,i,'heather')
handle_tts_kenny = lambda b,i: handle_tts(b,i,'kenny')
handle_tts_laura = lambda b,i: handle_tts(b,i,'laura')
handle_tts_nelly = lambda b,i: handle_tts(b,i,'nelly')
handle_tts_ryan = lambda b,i: handle_tts(b,i,'ryan')
handle_tts_r2d2 = lambda b,i: handle_tts(b,i,'r2d2')
handle_tts_en = lambda b,i: handle_tts(b,i,'en')

cmnds.add('tts', handle_tts_default, ['TTS', 'GUEST', 'USER'])
cmnds.add('tts-julia', handle_tts_julia, ['TTS', 'GUEST', 'USER'])
cmnds.add('tts-sarah', handle_tts_sarah, ['TTS', 'GUEST', 'USER'])
cmnds.add('tts-klaus', handle_tts_klaus, ['TTS', 'GUEST', 'USER'])
#cmnds.add('tts-de', handle_tts_de, ['TTS', 'GUEST', 'USER'])
cmnds.add('tts-lucy', handle_tts_lucy, ['TTS', 'GUEST', 'USER'])
cmnds.add('tts-peter', handle_tts_peter, ['TTS', 'GUEST', 'USER'])
cmnds.add('tts-rachel', handle_tts_rachel, ['TTS', 'GUEST', 'USER'])
cmnds.add('tts-heather', handle_tts_heather, ['TTS', 'GUEST', 'USER'])
cmnds.add('tts-kenny', handle_tts_kenny, ['TTS', 'GUEST', 'USER'])
cmnds.add('tts-laura', handle_tts_laura, ['TTS', 'GUEST', 'USER'])
cmnds.add('tts-nelly', handle_tts_nelly, ['TTS', 'GUEST', 'USER'])
cmnds.add('tts-ryan', handle_tts_ryan, ['TTS', 'GUEST', 'USER'])
cmnds.add('tts-r2d2', handle_tts_r2d2, ['TTS', 'GUEST', 'USER'])
#cmnds.add('tts-en', handle_tts_en, ['TTS', 'GUEST', 'USER'])
cmnds.add('tts-tail', handle_tts_tail, ['OPER'])
