# jsb/plugs/common/cprime.py
# -*- coding: utf-8 -*-
#

""" cprime plugin. """

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

RE_SEIN = re.compile(r'\b(bin|bist|gewesen|ist|sei|seid|seien|seiend|seiest|seiet|sein|sein sie|sein wir|seist|sind|war|waren|warst|wart|werde sein|werden sein|werdest sein|werdet sein|wird sein|wirst sein|wäre|wären|wärest|wäret|wärst|wärt|würde sein|würden sein|würdet sein)\b', re.IGNORECASE)

initdone = False

cfg = PersistConfig()
usermap = eval(open('%s/usermap' % cfg.get('datadir')).read())

## Cprime class

class Cprime(LazyDict):
    def __init__(self, rating=0):
        self.rating = rating
    pass

## CprimeItem class

class CprimeItem(PlugPersist):

    def __init__(self, name, default={}):
        PlugPersist.__init__(self, name)
        self.data.name = name
        self.data.rowcount = self.data.rowcount or 0.0
        self.data.cprimecount = self.data.cprimecount or 0.0

    def cprime(self):
        if self.data.rowcount == 0: return 0.0
        return float(self.data.cprimecount) / float(self.data.rowcount)
    
class CprimeList(UserState):

    def __init__(self, name, *args, **kwargs):
        UserState.__init__(self, name, "cprime", *args, **kwargs)
        if self.data.list: self.data.list = [LazyDict(x) for x in self.data.list]
        else: self.data.list = []
        self.name = name

    def add(self, txt):
        """ add a cprime """
        cprime = Cprime()
        cprime.txt = txt
        self.data.list.append(cprime)
        self.save()
        return len(self.data.list)

    def delete(self, indexnr):
        """ delete a cprime. """
        del self.data.list[indexnr-1]
        self.save()
        return self

    def clear(self):
        """ clear the cprime list. """
        self.data.list = []
        self.save()
        return self

    def increase(self):
        return self
    def decrease(self):
        return self

def init():
    global state
    global initdone
    state = PlugState()
    state.define('cprime', {})
    initdone = True
    return 1

## cprime-precondition

def precprime(bot, event):
    if event.userhost in bot.ignore: return False
    if len(event.txt) > 0 and event.txt[0] == '!': return False

    if (re.search(RE_SEIN, event.txt)):
        print "c-prime alarm"
        return True
    else:
        return False

## cprime-callbacks

def cprimecb(bot, event):
    event.bind(bot)

callbacks.add('PRIVMSG', cprimecb, precprime)
callbacks.add('MESSAGE', cprimecb, precprime)
callbacks.add('CONSOLE', cprimecb, precprime)
callbacks.add('CONVORE', cprimecb, precprime)

def getuser_old(event):
    return event.nick

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
    elif ievent.hostname and ievent.hostname.startswith('c-base/crew/'):
        return ievent.hostname[12:]
    elif ievent.hostname and ievent.hostname.startswith('pdpc/supporter/professional/'):
        return ievent.hostname[28:]
    elif ievent.auth.endswith('@shell.c-base.org'):
        return ievent.auth[1:-17]
    else:
        return ievent.nick

## cprime command

def handle_cprime(bot, event):
    """ show cprime of <nick>. """
    if not event.rest:
        item = getuser(event)
    else:
        item = event.rest.lower()

    print item
    i = CprimeItem(item)
    print i.data.cprimecount
    event.reply("%s has %f cprime." % (item, i.cprime()))

cmnds.add('cprime', handle_cprime, ['OPER', 'USER', 'GUEST'])
examples.add('cprime', 'show cprime', 'cprime jsb')

def handle_cprime_reset(bot, event):
    """reset cprimeemeter for user"""
    if not event.rest: event.missing("<nick>") ; return
    item = event.rest.lower()
    i = CprimeItem(item)
    i.data.rowcount = 0
    i.data.cprimecount = 0
    i.save()
    event.reply("cprime for %s has been desubjunctivised." % item)

cmnds.add('cprime-reset', handle_cprime_reset, ['OPER'])
