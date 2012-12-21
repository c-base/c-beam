# -*- coding: utf-8 -*-
# jsb.plugs.common/announce2342.py
#
#

""" announce 23:42. """

## jsb imports

from jsb.utils.exception import handle_exception
from jsb.lib.commands import cmnds
from jsb.lib.examples import examples
from jsb.utils.pdod import Pdod
from jsb.lib.datadir import getdatadir
from jsb.lib.persistconfig import PersistConfig
from jsb.lib.threads import start_new_thread
from jsb.lib.fleet import fleet
from jsb.lib.persist import PlugPersist
from jsb.lib.threadloop import TimedLoop

from jsb.lib.persist import PlugPersist

## basic imports

import os, time, datetime
import logging
import uuid
import jsonrpclib


cfg = PersistConfig()

# CONFIG SECTION #######################################################################

logindelta = 2342

cfg.define('watcher-interval', 5)
cfg.define('watcher-enabled', 0)
cfg.define('channel', "#c-base")

channel = "#c-base"

class Announce2342Error(Exception): pass

class Announce2342Watcher(TimedLoop):

    def handle(self):
        if not cfg.get('watcher-enabled'):
            raise Announce2342Error('watcher not enabled, use "!%s-cfg watcher-enabled 1" to enable' % os.path.basename(__file__)[:-3])
        #logging.warn("fleet: %s - %s" % (str(fleet), str(fleet.list())))
        #print "fleet: %s - %s" % (str(fleet), str(fleet.list()))
        bot = 0
        try: bot = fleet.byname(self.name)
        except: pass #print "fleet: %s" % str(fleet) #"fleet.byname(%s)" % self.name

        if bot != None:
            bot.connectok.wait()
        now = int(datetime.datetime.now().strftime("%H%M%S"))
        if now > 234200 and now <= 234205:
            bot.say(cfg.get('channel'), 'Es ist jetzt dreiundzwanzig Uhr zweiundvierzig.')
            time.sleep(2)
            bot.say(cfg.get('channel'), 'Oh.')
            #time.sleep(2)
            #bot.say(cfg.get('channel'), 'c-base++')

watcher = Announce2342Watcher('default-irc', cfg.get('watcher-interval'))

def init():
    watcher.start()
    return 1 

def shutdown():
    watcher.stop()
    return 1

def handle_announce2342(bot, ievent):
    ievent.reply('Es ist jetzt dreiundzwanzig Uhr zweiundvierzig.')
    time.sleep(2)
    ievent.reply('Oh.')


cmnds.add('announce2342', handle_announce2342, ['GUEST', 'USER'])
