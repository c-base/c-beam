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

    m = re.findall('(^|[^\w@])(c-?base)(\W|$)', event.txt, re.IGNORECASE)
    for match in m:
	if match[1] != 'c-base':
            if event.channel == '#c-base':
                #bot.say("#c-base", 'es heisst c-base und nicht '+match[1]+'. dance fu:r die beachtung aller sicherheitshinweise.')
                bot.say("#c-base", "it's c-base - NOT "+match[1]+', you '+insult())
            else:
                pass
            return True
    return False

def insult():
    s1 = ['dribbling ', 'snivelling ', 'braindead ', 'tentacled ', 'three eyed ', 'one dimensional ', 'borg loving ', 'slime sucking ', 'borg sniffing ', 'bug eyed ', 'single celled ', 'gargleblasting ', 'hallucinating ', '']
    s2 = ['', '', 'son of a ', 'clone of a ', 'excuse for a ', 'hologram of a ', 'apology for a ']
    s3 = ['', 'mutant ', 'parasitic ', 'vat-grown ', 'ferengi ', 'radiation damaged ', 'deranged ', 'space sick ', 'warp sick ', 'deviant ', 'clockwork ', 'useless ', 'superfluous ', 'stinking ' ]
    s4 = ['star goat', 'space weevil', 'toilet cleaning droid', 'bilge spore', 'nose worm', 'hyper slug', 'replicant', 'android', 'garbage droid', 'cyborg', 'pleasure droid', 'person', 'humanoid', 'bag of water', 'scumbag', 'idiot', 'douchebag', 'dumbass', 'collection of atoms']
    return random.choice(s1)+random.choice(s2)+random.choice(s3)+random.choice(s4)+"!"


## corrector-callbacks

def correctorcb(bot, event):
    event.bind(bot)

callbacks.add('PRIVMSG', correctorcb, precorrector)
callbacks.add('MESSAGE', correctorcb, precorrector)
callbacks.add('CONSOLE', correctorcb, precorrector)
callbacks.add('CONVORE', correctorcb, precorrector)

## corrector command

def handle_corrector(bot, ievent):
    insult_text = ievent.nick + ": you are are " + insult()
    if len(ievent.rest) > 0 and re.search("c-beam", ievent.rest, re.IGNORECASE) == None:
        insult_text = ievent.rest + " is a " + insult()

    if ievent.channel == "#c-base":
        bot.say(ievent.channel, insult_text)
        pass
    else:
        ievent.reply(insult_text)

cmnds.add('insult', handle_corrector, ['OPER', 'USER', 'GUEST'])
