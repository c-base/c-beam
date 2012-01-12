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

from icalendar.cal import Calendar, Event

## defines

channel = "#c-base"
events = []

cfg = PersistConfig()
cfg.define('watcher-interval', 5)
cfg.define('watcher-enabled', 0)
cfg.define('channel', "#c-base")

class EventError(Exception): pass

class EventWatcher(TimedLoop):

    def handle(self):
        if not cfg.get('watcher-enabled'):
            raise EventError('watcher not enabled, use "!%s-cfg watcher-enabled 1" to enable' % os.path.basename(__file__)[:-3])
        #logging.info("fleet: %s - %s" % (str(fleet), str(fleet.list())))
        bot = 0
        try: bot = fleet.byname(self.name)
        except: print "fleet: %s" % str(fleet) #"fleet.byname(%s)" % self.name

        bot.connectok.wait()
        now = int(datetime.datetime.now().strftime("%H%M%S"))
        if now > 030000 and now <= 030005:
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

def getcal():
    conn = httplib.HTTPConnection("community.c-base.org")
    conn.request("GET", "/commcal.php")
    r1 = conn.getresponse()
    cal = Calendar.from_string(r1.read())
    return cal

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
    cal = getcal()
    events = []
    for event in cal.walk('vevent'):
        if str(event['dtstart']).startswith(datetime.datetime.now().strftime("%Y%m%d")):
            #start = int(str(event['dtstart'])[-7:-3])+200) % 2400
            #events.append("%s [%s]" % (event['summary'], int(start[-7:-3])+200))
            events.append(event['summary'].replace("|", "/"))
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
    cal = getcal()
    events = []
    for event in cal.walk('vevent'):
        if str(event['dtstart']).startswith(datetime.datetime.now().strftime("%Y%m%d")):
            #start = int(str(event['dtstart'])[-7:-3])+200) % 2400
            #events.append("%s [%s]" % (event['summary'], int(start[-7:-3])+200))
            events.append(event['summary'].replace("|", "/"))
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
        cal = getcal()
        #for event in cal.walk('vevent'): print event['summary'] if e
        #ievent.reply("na:chster event: %s" % event ) 
    except: pass

def handle_today(bot, ievent):
    cal = getcal()
    eventcounter = 0
    for event in cal.walk('vevent'):
        if str(event['dtstart']).startswith(datetime.datetime.now().strftime("%Y%m%d")):
            ievent.reply("%s - %s" % (event['summary'], event['dtstart']))
            eventcounter += 1
    if eventcounter == 0:
            ievent.reply("für heute sind leider keine events eingetragen")

cmnds.add('events', handle_today, ['GUEST', 'USER'])
cmnds.add('events-today', handle_today, ['GUEST', 'USER'])


