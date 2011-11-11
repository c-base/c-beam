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
from jsb.lib.persistconfig import PersistConfig

## basic imports

import logging
import re

## defines

RE_PRONOUN = re.compile(r'jemand|irgendwer|man|einer', re.IGNORECASE)
RE_CONJUNCTIVE = re.compile(r'sollte|m\xfcsste|muesste|k\xf6nnte|koennte|h\xe4tte|haette|br\xe4uchte|braeuchte', re.IGNORECASE)



cfg = PersistConfig()
usermap = eval(open('%s/usermap' % cfg.get('datadir')).read())

## HubelItem class

class HubelItem(PlugPersist):

    def __init__(self, name, default={}):
        PlugPersist.__init__(self, name)
        self.data.name = name
        self.data.rowcount = self.data.rowcount or 0.0
        self.data.hubelcount = self.data.hubelcount or 0.0

    def hubel(self):
        if self.data.rowcount == 0: return 0.0
        return float(self.data.hubelcount) / float(self.data.rowcount)
      
## hubelmeter-precondition

def prehubelmeter(bot, event):
     # if not event.iscmnd(): return False
     # we want to catch all the ++ and to avoid cheating
    if event.userhost in bot.ignore: return False
    if len(event.txt) > 0 and event.txt[0] == '!': return False
    pronoun = re.search(RE_PRONOUN, event.txt)
    conjunctive = re.search(RE_CONJUNCTIVE, event.txt)

    i = HubelItem(getuser(event))
    # increase linecounter only
    i.data.rowcount += 1.0
    if pronoun and conjunctive:
        # increase hubelcounter
        i.data.hubelcount += 1.0
        i.save()
        if event.channel != '#c-base':
            event.reply('hubel detected from %s' % getuser(event))
        print 'hubel detected from %s' % getuser(event)
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

## hubelmeter command

def handle_hubelmeter(bot, event):
    """ show hubelmeter of <nick>. """
    if not event.rest:
        item = getuser(event)
    else:
        item = event.rest.lower()

    print item
    i = HubelItem(item)
    print i.data.hubelcount
    event.reply("%s has %f hubel." % (item, i.hubel()))

cmnds.add('hubelmeter', handle_hubelmeter, ['OPER', 'USER', 'GUEST'])
examples.add('hubelmeter', 'show hubelmeter', 'hubelmeter jsb')

def handle_hubelmeter_reset(bot, event):
    """reset hubelemeter for user"""
    if not event.rest: event.missing("<nick>") ; return
    item = event.rest.lower()
    i = HubelItem(item)
    i.data.rowcount = 0
    i.data.hubelcount = 0
    i.save()
    event.reply("hubelmeter for %s has been neutralized." % item)

cmnds.add('hubelmeter-reset', handle_hubelmeter_reset, ['OPER'])
