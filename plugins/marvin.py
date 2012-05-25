# jsb/plugs/common/marvin.py
# -*- coding: utf-8 -*-
#

""" marvin plugin. """

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

#RE_STRONGPRONOUN = re.compile(r'\b(man|bernd)\b', re.IGNORECASE)


quotes = {
    "life": "Life! Don't talk to me about life.",
}

initdone = False

cfg = PersistConfig()

def init():
    global state
    global initdone
    #state = PlugState()
    #state.define('hubel', {})
    initdone = True
    return 1

## marvin-precondition

def premarvin(bot, event):
    if event.userhost in bot.ignore: return False
    if len(event.txt) > 0 and event.txt[0] == '!': return False


    for key in quotes.keys():
        if re.search(key, event.txt):
            event.reply(quotes[key])
            return True
    return False

## marvin-callbacks

def marvincb(bot, event):
    event.bind(bot)

callbacks.add('PRIVMSG', marvincb, premarvin)
callbacks.add('MESSAGE', marvincb, premarvin)
callbacks.add('CONSOLE', marvincb, premarvin)
callbacks.add('CONVORE', marvincb, premarvin)

## marvin command

def handle_marvin(bot, event):
    warning = random.choice(quotes.values())
    if ievent.channel == "#c-base":
        bot.say(ievent.channel, warning)
    else:
        ievent.reply(warning)

cmnds.add('marvin', handle_marvin, ['OPER', 'USER', 'GUEST'])
