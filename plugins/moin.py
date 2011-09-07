# jsb/plugs/common/moin.py
#
#

""" run the eight ball. """

## jsb imports

from jsb.utils.exception import handle_exception
from jsb.lib.commands import cmnds
from jsb.lib.examples import examples
from jsb.lib.persistconfig import PersistConfig

## basic imports

import re
import random

## defines

cfg = PersistConfig()

usermap = eval(open('%s/usermap' % cfg.get('datadir')).read())

text=[
    "gru:Ce %s, wie geht es dir?",
    "gru:Ce %s!",
    "remoin %s.",
    "moinsen %s.",
    "darf ich dir einen maffee anbieten %s?",
    ]

## moin command

def getuser(ievent):
    if ievent.channel in usermap:
        return usermap[ievent.channel]
    elif ievent.fromm and ievent.fromm in usermap:
        return usermap[ievent.fromm]
    elif ievent.nick and ievent.nick in usermap:
        return usermap[ievent.nick]
    elif ievent.ruserhost in usermap:
        return usermap[ievent.ruserhost]
    elif ievent.auth.endswith('@shell.c-base.org'):
        return ievent.auth[1:-17]
    elif ievent.channel.find('@c-base.org') > -1:
        return ievent.channel[:-11]
    elif ievent.fromm and ievent.fromm.find('c-base.org') > -1:
        return ievent.fromm[:-10]
    elif ievent.hostname and ievent.hostname.startswith('c-base/crew/'):
        return ievent.hostname[12:]
    elif ievent.hostname and ievent.hostname.startswith('pdpc/supporter/professional/'):
        return ievent.hostname[28:]
    else:
        return ievent.nick

def handle_moin(bot, ievent):
    """ throw the eight ball. """
    
    ievent.reply(random.choice(text) % getuser(ievent))

cmnds.add('moin', handle_moin, ['OPER', 'USER', 'GUEST'])
examples.add('moin', 'show what the magic 8 ball has to say.', 'moin')
