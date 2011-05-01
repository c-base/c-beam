# -*- coding: utf-8 -*-
# jsb.plugs.common/tts.py
#
#

""" run the eight ball. """

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

## defines


cfg = PersistConfig()
cfg.define('rpcurl', 'http://10.0.1.13:1775')
cfg.define('local', False)

usermap = eval(open('%s/usermap' % cfg.get('datadir')).read())
ttslog = '%s/botlogs/tts.log' % cfg.get('datadir')

jsonrpclib.config.version = 1.0
server = jsonrpclib.Server(cfg.get('rpcurl'))

def getuser(ievent):
    if ievent.channel in usermap:
        return usermap[ievent.channel]
    elif ievent.fromm in usermap:
        return usermap[ievent.fromm]
    else:
        return ievent.channel

## tts command

def handle_tts(bot, ievent, voice):
    """ text to speech synthesis. """
    if not ievent.args:
        ievent.missing('text')
        return
    
    text = urllib.quote(ievent.rest)
    #text.replace('$','Dollar')
    
    try:
        if cfg.get('local'):
            #os.system("echo %s | festival --tts" % ievent.rest)
            os.system("tts.py %s %s | xargs mpg123" % (voice, text))
        else:
            server.tts(voice, text)
             
    except:
        ievent.reply(str(sys.exc_info()[0]))
    try:
        f = open(ttslog, 'a')
        f.write('%s: %s (%s)\n' % (getuser(ievent), ievent.rest, voice))
        f.close()
    except:
        ievent.reply(str(sys.exc_info()[0]))

handle_tts_default = lambda b,i: handle_tts(b,i,'lucy')
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
handle_tts_en = lambda b,i: handle_tts(b,i,'en')

cmnds.add('tts', handle_tts_default, ['USER', 'GUEST'])
examples.add('tts', 'show what the magic 8 ball has to say.', 'tts')
cmnds.add('tts-julia', handle_tts_julia, ['USER', 'GUEST'])
cmnds.add('tts-sarah', handle_tts_sarah, ['USER', 'GUEST'])
cmnds.add('tts-klaus', handle_tts_klaus, ['USER', 'GUEST'])
cmnds.add('tts-de', handle_tts_de, ['USER', 'GUEST'])
cmnds.add('tts-lucy', handle_tts_lucy, ['USER', 'GUEST'])
cmnds.add('tts-peter', handle_tts_peter, ['USER', 'GUEST'])
cmnds.add('tts-rachel', handle_tts_rachel, ['USER', 'GUEST'])
cmnds.add('tts-heather', handle_tts_heather, ['USER', 'GUEST'])
cmnds.add('tts-kenny', handle_tts_kenny, ['USER', 'GUEST'])
cmnds.add('tts-laura', handle_tts_laura, ['USER', 'GUEST'])
cmnds.add('tts-nelly', handle_tts_nelly, ['USER', 'GUEST'])
cmnds.add('tts-ryan', handle_tts_ryan, ['USER', 'GUEST'])
cmnds.add('tts-en', handle_tts_en, ['USER', 'GUEST'])
