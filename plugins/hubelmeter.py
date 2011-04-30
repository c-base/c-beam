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

RE_KARMA = re.compile(r'^(?P<item>\([^\)]+\)|\[[^\]]+\]|\w+)(?P<mod>\+\+|--)( |$)')
RE_PRONOUN = re.compile(r'jemand|irgendwer|man|einer')
RE_CONJUNCTIVE = re.compile(r'sollte|müsste|könnte|hätte')

## hubelmeter-precondition

def prehubelmeter(bot, event):
     # if not event.iscmnd(): return False
     # we want to catch all the ++ and to avoid cheating
    if event.userhost in bot.ignore: return False
    pronoun = re.search(RE_PRONOUN, event.txt)
    conjunctive = re.search(RE_CONJUNCTIVE, event.txt)

    if pronoun and conjunctive:
        # increase hubelcounter and linecounter
        print "hubel!!1elf"
        return True
    else:
        # increase linecounter only
        return False

## hubelmeter-callbacks

def hubelmetercb(bot, event):
    event.bind(bot)

callbacks.add('PRIVMSG', hubelmetercb, prehubelmeter)
callbacks.add('MESSAGE', hubelmetercb, prehubelmeter)
callbacks.add('CONSOLE', hubelmetercb, prehubelmeter)
callbacks.add('CONVORE', hubelmetercb, prehubelmeter)

## hubelmeter command

def handle_hubelmeter(bot, event):
    """ show hubelmeter of item. """
    if not event.rest: event.missing("<what>") ; return
    k = event.rest.lower()
    item = KarmaItem(event.channel.lower() + "-" + k)
    if item.data.count: event.reply("hubelmeter of %s is %s" % (k, item.data.count))
    else: event.reply("%s doesn't have hubelmeter yet." % k)

cmnds.add('hubelmeter', handle_hubelmeter, ['OPER', 'USER', 'GUEST'])
examples.add('hubelmeter', 'show hubelmeter', 'hubelmeter jsb')
