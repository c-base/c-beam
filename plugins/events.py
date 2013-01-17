# -*- coding: utf-8 -*-
# jsb.plugs.common/koffie.py
#
# Made by WildRover and Junke1990

""" schenk wat koffie! """

## jsb imports

from jsb.lib.commands import cmnds
from jsb.lib.examples import examples
from jsb.lib.persistconfig import PersistConfig
from jsb.lib.threadloop import TimedLoop
from jsb.lib.fleet import fleet

## basic imports

import os
import string
import random
import httplib
import datetime
import re
#import jsonrpclib
from jsonrpc.proxy import ServiceProxy


## defines

channel = "#c-base"
events = []

cfg = PersistConfig()
cfg.define('watcher-interval', 5)
cfg.define('watcher-enabled', 0)
cfg.define('channel', "#c-base")

cfg.define('c-beam-url', 'http://127.0.0.1:4254/rpc/')

##
#jsonrpclib.config.version = 1.0
#server = jsonrpclib.Server(cfg.get('c-beam-url'))
server = ServiceProxy(cfg.get('c-beam-url'))

class EventError(Exception): pass

class EventWatcher(TimedLoop):

    def handle(self):
        if not cfg.get('watcher-enabled'):
            raise EventError('watcher not enabled, use "!%s-cfg watcher-enabled 1" to enable' % os.path.basename(__file__)[:-3])
        #logging.info("fleet: %s - %s" % (str(fleet), str(fleet.list())))
        bot = 0
        try: bot = fleet.byname(self.name)
        except: pass #print "fleet: %s" % str(fleet) #"fleet.byname(%s)" % self.name

        if bot != None:
            bot.connectok.wait()
        now = int(datetime.datetime.now().strftime("%H%M%S"))
        #print now
        if now > 60000 and now <= 60005:
            print ">>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>setting topic"
            settopic(bot, "#c-base")

watcher = EventWatcher('default-irc', cfg.get('watcher-interval'))

## init function

def init():
    watcher.start()
    return 1

def shutdown():
    watcher.stop()
    return 1

## functions

## commands

def checktopicmode(bot, ievent):
    """ callback for change in channel topic mode """
    chan = ievent.channel
    mode = ievent.chan.data.mode
    if mode and 't' in mode:
        if chan not in bot.state['opchan']:
            ievent.reply("i'm not op on %s" % chan)
            return 0
    return 1


def handle_event_topic(bot, ievent):
    if not bot.jabber and not checktopicmode(bot, ievent): return
    result = settopic(bot, ievent.channel)
    return ievent.reply(result)

    """ event-topic .. add todays events to the topic """
    if not bot.jabber and not checktopicmode(bot, ievent): return
    result = bot.gettopic(ievent.channel)
    what = result[0]
    #what += " | %s" % ievent.rest
    # remopve old events
    what = re.sub(r' \| heute an bord\: .* \|', ' |', what)
    what = re.sub(r' \| heute an bord\: .*', '', what)
    events = server.events()['result']
    if len(events) > 0:
        what += " | heute an bord: %s" % ", ".join(events) 
    if what != result[0]:
        bot.settopic(ievent.channel, what)
    else:
        ievent.reply('das topic ist bereits auf dem aktuellen stand.')

cmnds.add('event-topic', handle_event_topic, ['OPER'])

def settopic(bot, channel):
    """ event-topic .. add todays events to the topic """
    result = bot.gettopic(channel)
    if not result: return 'topic connte nicht ausgelesen werden'
    what = result[0]
    what = re.sub(r' \| heute an bord\: .* \|', ' |', what)
    what = re.sub(r' \| heute an bord\: .*', '', what)
    events = server.events()['result']
    if len(events) > 0:
        what += " | heute an bord: %s" % ", ".join(events) 
    if what != result[0]:
        bot.settopic(channel, what)
    else:
        return 'das topic ist bereits auf dem aktuellen stand.'

def handle_events(bot, ievent):
    """ get a events """
    try:
        now = datetime.datetime.now().strftime("%H%M%S")
        today = datetime.datetime.now().strftime("%Y%m%d")
        #for event in cal.walk('vevent'): print event['summary'] if e
        #ievent.reply("na:chster event: %s" % event ) 
    except: pass

def handle_today(bot, ievent):
    events = server.events()['result']
    if len(events) > 0:
        ievent.reply(' | '.join(events))
    else:
        ievent.reply("für heute sind leider keine events eingetragen")

cmnds.add('events', handle_today, ['GUEST', 'USER'])
cmnds.add('events-today', handle_today, ['GUEST', 'USER'])


