# jsb.plugs.common/cbeam.py
#
#

## jsb imports

from jsb.lib.callbacks import callbacks
from jsb.lib.commands import cmnds
from jsb.lib.examples import examples
from jsb.lib.persist import PlugPersist
from jsb.utils.statdict import StatDict
from jsb.lib.datadir import getdatadir
from jsb.utils.thomas import Bayes

## basic imports

import logging
import time
import random

## defines

messages=[
    "0100110010100101000110011000101001100011110001010011000100110001010110000110001010101100110101100100101000110001010011000101001111000010101010001001001100110011001001010101100011110010101001000000000000101010011001100101011000101011000101000111001010101001110001010101100011100101010011110001100101010011001011000100100010111001010110101100100010100100100100100100100010001000100001010101110011010101100111010100100",
    "Der Wissensstand wurde nicht vollsta:ndig reconstruiert"
    ]

## cbeam precondition

def precbeam(bot, event):
    if event.userhost in bot.ignore: return False

    print 'c-beam for %s' % event.userhost
    if len(event.txt) > 2 and event.txt[0] not in event.chan.data.cc:
        return True
    return False

## cbeam callbacks

def cbeamcb(bot, event):
    event.bind(bot)
    time.sleep(1)
    event.reply(random.choice(messages))
    return 0

callbacks.add('PRIVMSG', cbeamcb, precbeam)
callbacks.add('MESSAGE', cbeamcb, precbeam)
callbacks.add('CONSOLE', cbeamcb, precbeam)

def handle_cbeam(bot, event):
    event.reply(random.choice(messages))

cmnds.add('c-beam', handle_cbeam, ['GUEST', ])
