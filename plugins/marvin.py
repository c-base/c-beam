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
    "life": [
        "Life! Don't talk to me about life.",
        "Ha, but my life is but a box of wormgears.",
        "Life...loathe it or ignore it, you can't like it.",
        "Funny how just when you think life can't possibly get any worse it suddenly does.",
        
    ],
    "feeling": ["I think you ought to know I'm feeling very depressed"],
    "c-beam.*doof": ["Sorry, did I say something wrong?"],
    "spare parts|ersatzteile": ["I'm all spare parts"],
    "intelligence": ["Wearily I sit here, pain and misery my only companions. And vast intelligence of course. And infinite sorrow."],
    "diodes|dioden": ["And then of course I've got this terrible pain in all the diodes down my left side."],
    "hallo.*c-beam": ["Don't pretend you want to talk to me, I know you hate me."],
    "enjoy": ["The first ten million years were the worst, and the second ten million years, they were the worst too. The third million years I didn't enjoy at all. After that I went into a bit of decline."],
    "rosten|corner": ["Do you want me to sit in a corner and rust, or just fall apart where I'm standing?"], 
    "ruhe.*c-beam|schnauze.*c-beam|sei leise c-beam": ["Do you want me to sit in a corner and rust, or just fall apart where I'm standing?"], 
    #"feierabend": ["Why stop now just when I'm hating it?"],
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
            if event.channel == '#c-base':
                bot.say("#c-base", random.choice(quotes[key]))
            else:
                event.reply(random.choice(quotes[key]))
            return True
    #if re.match(r'^so+.?$', event.txt) and event.nick == "bronsen":
        #bot.say("#c-base", random.choice(quotes[key]))
       
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
