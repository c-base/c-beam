# jsb/plugs/common/corrector.py
# -*- coding: utf-8 -*-
#

""" corrector plugin. """

## jsb imports

from jsb.lib.callbacks import callbacks
from jsb.lib.commands import cmnds
from jsb.lib.examples import examples
from jsb.lib.persist import PlugPersist
from jsb.utils.statdict import StatDict
from jsb.lib.persistconfig import PersistConfig
from jsb.lib.persiststate import UserState
from jsb.utils.lazydict import LazyDict


## basic imports

import logging
import re
import random
from jsb.lib.persiststate import PlugState

## defines

initdone = False

cfg = PersistConfig()

def init():
    global state
    global initdone
    #state = PlugState()
    #state.define('hubel', {})
    initdone = True
    return 1

## corrector-precondition

def precorrector(bot, event):
    if event.userhost in bot.ignore: return False
    if len(event.txt) > 0 and event.txt[0] == '!': return False

    m = re.findall('(^|\W)(c-?base)(\W|$)', event.txt, re.IGNORECASE)
    for match in m:
	if match[1] != 'c-base':
        c.privmsg(target, "It's c-base, not "+match[1]+'. '+random.choice(INSULTS))
        if event.channel == '#c-base':
            bot.say("#c-base", 'es heisst c-base und nicht '+match[1]+'. dance fu:r die beachtung aller sicherheitshinweise.')
        else:
            pass
        return True
    return False

## corrector-callbacks

def correctorcb(bot, event):
    event.bind(bot)

callbacks.add('PRIVMSG', correctorcb, precorrector)
callbacks.add('MESSAGE', correctorcb, precorrector)
callbacks.add('CONSOLE', correctorcb, precorrector)
callbacks.add('CONVORE', correctorcb, precorrector)

## corrector command

def handle_corrector(bot, event):
    warning = random.choice(quotes.values())
    if ievent.channel == "#c-base":
        bot.say(ievent.channel, warning)
    else:
        ievent.reply(warning)

#cmnds.add('corrector', handle_corrector, ['OPER', 'USER', 'GUEST'])
