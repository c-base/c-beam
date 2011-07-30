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

    logging.info('c-beam for %s' % event.userhost)
    if len(event.txt) > 2 and event.txt[0] not in event.chan.data.cc:
        if event.channel == "#c-base":
            return False
        elif event.channel == "#c-beam":
            return False
        elif event.channel == "#c-base-bots":
            if "c-beam" in event.txt:
                return True
            else:
                return False
        else:
            return True
        return False
    return False

## cbeam callbacks

def cbeamcb(bot, event):
    event.bind(bot)
    time.sleep(1)
    if event.txt.find('help') != -1:
        event.reply('http://bit.ly/c-beam')
    else:
        event.reply(random.choice(messages))
    return 0

callbacks.add('PRIVMSG', cbeamcb, precbeam)
callbacks.add('MESSAGE', cbeamcb, precbeam)
callbacks.add('CONSOLE', cbeamcb, precbeam)

def handle_cbeam(bot, event):
    event.reply(random.choice(messages))

cmnds.add('c-beam', handle_cbeam, ['GUEST', ])
