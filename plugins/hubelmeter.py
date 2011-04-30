# jsb/plugs/common/hubelmeter.py
# -*- coding: utf-8 -*-
#

""" hubelmeter plugin. """

## jsb imports

from jsb.lib.callbacks import callbacks
from jsb.lib.commands import cmnds
from jsb.lib.examples import examples
from jsb.lib.persist import PlugPersist
from jsb.utils.statdict import StatDict

## basic imports

import logging
import re

## defines

RE_PRONOUN = re.compile(r'jemand|irgendwer|man|einer')
RE_CONJUNCTIVE = re.compile(r'sollte|m.sste|k.nnte|h.tte')

## HubelItem class

class HubelItem(PlugPersist):

    def __init__(self, name, default={}):
        PlugPersist.__init__(self, name)
        self.data.name = name
        self.data.rowcount = self.data.rowcount or 0.0
        self.data.hubelcount = self.data.hubelcount or 0.0

    def hubel(self):
        print self.data.hubelcount
        print  self.data.rowcount
        return float(self.data.hubelcount) / float(self.data.rowcount)
      
## hubelmeter-precondition

def prehubelmeter(bot, event):
     # if not event.iscmnd(): return False
     # we want to catch all the ++ and to avoid cheating
    if event.userhost in bot.ignore: return False
    if len(event.txt) > 0 and event.txt[0] == '!': return False
    pronoun = re.search(RE_PRONOUN, event.txt)
    conjunctive = re.search(RE_CONJUNCTIVE, event.txt)

    print pronoun
    print conjunctive
    i = HubelItem(getuser(event))
    # increase linecounter only
    i.data.rowcount += 1.0
    if pronoun and conjunctive:
        # increase hubelcounter
        i.data.hubelcount += 1.0
        i.save()
        print "hubel!!1elf"
        event.reply('HUBEL!!1elf')
        return True
    else:
        i.save()
        return False

## hubelmeter-callbacks

def hubelmetercb(bot, event):
    event.bind(bot)

callbacks.add('PRIVMSG', hubelmetercb, prehubelmeter)
callbacks.add('MESSAGE', hubelmetercb, prehubelmeter)
callbacks.add('CONSOLE', hubelmetercb, prehubelmeter)
callbacks.add('CONVORE', hubelmetercb, prehubelmeter)

def getuser(event):
    return event.nick

## hubelmeter command

def handle_hubelmeter(bot, event):
    """ show hubelmeter of item. """
    if not event.rest:
        item = getuser(event)
        #event.missing("<what>") ; return
    else:
        item = event.rest.lower()

    print item
    i = HubelItem(item)
    print i.data.hubelcount
    event.reply("%s has %f hubel." % (item, i.hubel()))

cmnds.add('hubelmeter', handle_hubelmeter, ['OPER', 'USER', 'GUEST'])
examples.add('hubelmeter', 'show hubelmeter', 'hubelmeter jsb')
