# jsb.plugs.common/eta.py
#
#

""" list all available users. """

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

## basic imports

import re, random
import os, time

cfg = PersistConfig()
cfg.define('watcher-interval', 5)
cfg.define('watcher-enabled', 0)
cfg.define('eta-timeout', 72000)

userpath = '/home/smile/users'
usermap = eval(open('%s/usermap' % cfg.get('datadir')).read())

class EtaItem(PlugPersist):
     def __init__(self, name, default={}):
         PlugPersist.__init__(self, name)
         self.data.name = name
         self.data.etas = self.data.etas or {}
         self.data.etatimestamps = self.data.etatimestamps or {}
         self.data.etasubs = self.data.etasubs or []
         self.data.opensubs = self.data.opensubs or []

etaitem = EtaItem('eta')

class UserlistError(Exception): pass

class UserlistWatcher(Pdod):
    def __init__(self):
        Pdod.__init__(self, os.path.join(getdatadir() + os.sep + 'plugs' + os.sep + 'jsb.plugs.sockets.eta', 'eta'))
        self.running = False

    def add(self, bot, ievent):
        if not self.has_key2(bot.name, ievent.channel):
            self.set(bot.name, ievent.channel, True)
            self.save()

    def remove(self, bot, ievent):
        if self.has_key2(bot.name, ievent.channel):
            del self.data[bot.name][ievent.channel]
            self.save()

    def start(self):
        self.running = True
        start_new_thread(self.watch, ())

    def stop(self):
        self.running = False

    def watch(self):
        if not cfg.get('watcher-enabled'):
            raise UserlistError('watcher not enabled, use "!%s-cfg watcher-enabled 1" to enable' % os.path.basename(__file__)[:-3])
        lastcount = -1
        lasteta = -1
        lastuserlist = userlist()
        while self.running:
            if self.data:
                try:
                    # check if at least one user is logged in
                    # or try to ping the switches
                    users = userlist()
                    usercount = len(users)
                    if usercount != lastcount or lasteta != len(etaitem.data.etas):
                        if lastcount == 0 and usercount > 0:
                            print str(self.data.keys())
                            for name in self.data.keys():
                                bot = fleet.byname(name)
                                print name
                                print str(bot)
                                if bot and bot.type == "sxmpp":
                                    for opensub in etaitem.data.opensubs:
                                        bot.say(opensub, 'c3pO is awake')
                        lastcount = usercount
                        lasteta = len(etaitem.data.etas)

                        print 'Usercount: %s' % usercount
                        if usercount > 0:
                            self.announce('open', 'chat')
                            # check if someone arrived who set an ETA
                            for user in users:
                                try: 
                                    del etaitem.data.etas[user]
                                    etaitem.save()
                                except: pass

                            # find out who just arrived
                            newusers = []
                            for user in userlist():
                                if user not in lastuserlist:
                                    newusers.append(user)
                            #tell subscribers who has just arrived
                            for user in newusers:
                                print '%s has just arrived!' % user
                            lastuserlist = userlist()
                        else:
                            if len(etaitem.data.etas) > 0:
                                self.announce('incoming', 'dnd')
                            else:
                                self.announce('closed', 'xa')

                    # remove expired ETAs
                    for user in etaitem.data.etas.keys():
                        if time.time() > etaitem.data.etatimestamps[user]:
                            del etaitem.data.etas[user]
                            del etaitem.data.etatimestamps[user]
                            etaitem.save()

                except UserlistError:
                    pass
                except KeyError:
                    pass
            time.sleep(cfg.get('watcher-interval'))

    def announce(self, status, show):
        if not self.running or not cfg.get('watcher-enabled'):
            return
        for name in self.data.keys():
            bot = 0
            try: bot = fleet.byname(name)
            except: pass
            if bot and bot.type == "sxmpp":
                for channel in self.data[name].keys():
                    print "account %s %s %s" % (status, show, channel)
                    bot.setstatus(status, show)

watcher = UserlistWatcher()
if not watcher.data:
    watcher = UserlistWatcher()

def init():
    if cfg.get('watcher-enabled'):
        watcher.start()
    return 1

def shutdown():
    if watcher.running:
        watcher.stop()
    return 1

def userlist():
    return os.listdir(userpath)

## eta command

def handle_eta(bot, ievent):
    """list all user that have logged in on the mirror."""
    users = userlist()
    reply = ''
    if len(users) > 0 or len(etaitem.data.etas) > 0:
        if len(users) > 0:
            reply += 'available: ' + ', '.join(users) + '\n' 
        if len(etaitem.data.etas) > 0:
            etalist = []
            for key in etaitem.data.etas.keys():
                etalist += ['%s (%s)' % (key, etaitem.data.etas[key])]
            reply += 'ETA: ' + ', '.join(etalist) + '\n'
    else:
        reply = "No one there"
    ievent.reply(reply)

def handle_eta_login(bot, ievent):
    try:
        result = os.system('touch %s/%s' % (userpath, usermap[ievent.channel]))
        ievent.reply('Login result: %s' % result)
    except UserlistError, e:
        ievent.reply(str(s))

def handle_eta_logout(bot, ievent):
    try:
        result = os.remove('%s/%s' % (userpath, usermap[ievent.channel]))
        ievent.reply('Logout result: %s' % result)
    except UserlistError, e:
        ievent.reply(str(s))

def handle_eta_subeta(bot, ievent):
    try:
        if ievent.channel not in etaitem.data.etasubs:
            etaitem.data.etasubs.append(ievent.channel)
            etaitem.save()
        ievent.reply('thank you for your subscription for eta notifications')
    except UserlistError, e:
        ievent.reply(str(s))

def handle_eta_unsubeta(bot, ievent):
    try:
        if ievent.channel in etaitem.data.etasubs:
            print 'remove %s from %s' % (ievent.channel, str(etaitem.data.etasubs))
            etaitem.data.etasubs.remove(ievent.channel)
            etaitem.save()
        ievent.reply('you have been unsubscribed from eta notifications')
    except UserlistError, e:
        ievent.reply(str(s))
   
def handle_eta_subopen(bot, ievent):
    try:
        if ievent.channel not in etaitem.data.opensubs:
            etaitem.data.opensubs.append(ievent.channel)
            etaitem.save()
        ievent.reply('thank you for your opening notification subscription')
    except UserlistError, e:
        ievent.reply(str(s))

def handle_eta_unsubopen(bot, ievent):
    try:
        if ievent.channel in etaitem.data.opensubs:
            print 'remove %s from %s' % (ievent.channel, str(etaitem.data.opensubs))
            etaitem.data.opensubs.remove(ievent.channel)
            etaitem.save()
        ievent.reply('you have been unsubscribed from opening notifications')
    except UserlistError, e:
        ievent.reply(str(s))
    
def handle_eta_lssub(bot, ievent):
    try:
        ievent.reply('ATT-Subbscribers: %s\nOpening Subscribers: %s\nETA-Subscribers: %s' % (str(etaitem.data.subscribers), str(etaitem.data.opensubs), str(etaitem.data.etasubs)))
    except UserlistError, e:
        ievent.reply(str(s))

def handle_eta_lseta(bot, ievent):
    try:
        if len(etaitem.data.etas) > 0:
            etalist = []
            for key in etaitem.data.etas.keys():
                etalist += ['%s (%s)' % (key, etaitem.data.etas[key])]
            ievent.reply('ETA: %s' % ', '.join(etalist))
    except UserlistError, e:
        ievent.reply(str(s))

def handle_eta_eta(bot, ievent):
    eta = 0
    try:    eta = int(ievent.args[0])
    except: pass
    if ievent.channel in usermap.keys():
        user = usermap[ievent.channel]
    else:
        user = ievent.channel
        if ievent.channel == 'c3pb@conference.c3pb.de':
            #ievent.reply("This does not work :P")
            print "This does not work :P"
        else:
            ievent.reply("I don't know your nickname, you should contact my owner")
        return 0
    if eta == 0:
        del etaitem.data.etas[user]
    else:
        etaitem.data.etas[user] = eta
        etaitem.data.etatimestamps[user] = time.time() + cfg.get('eta-timeout')
    etaitem.save()
    try:
        for etasub in etaitem.data.etasubs:
            bot.say(etasub, 'ETA %s %d' % (user, eta))
        #ievent.reply('Set eta for %s to %d' % (user, eta))
        ievent.reply('Danke dass Du bescheid sagst :)')
 
    except UserlistError, e:
        ievent.reply(str(s))

def handle_eta_watch_start(bot, ievent):
    if not cfg.get('watcher-enabled'):
        ievent.reply('watcher not enabled, use "!%s-cfg watcher-enabled 1" to enable and reload the plugin' % os.path.basename(__file__)[:-3])
        return
    watcher.add(bot, ievent)
    ievent.reply('ok')

def handle_eta_watch_stop(bot, ievent):
    if not cfg.get('watcher-enabled'):
        ievent.reply('watcher not enabled, use "!%s-cfg watcher-enabled 1" to enable and reload the plugin' % os.path.basename(__file__)[:-3])
        return
    watcher.remove(bot, ievent)
    ievent.reply('ok')

def handle_eta_watch_list(bot, ievent):
    if not cfg.get('watcher-enabled'):
        ievent.reply('watcher not enabled, use "!%s-cfg watcher-enabled 1" to enable and reload the plugin' % os.path.basename(__file__)[:-3])
        return
    result = []
    for name in sorted(watcher.data.keys()):
        if watcher.data[name]:
            result.append('on %s:' % name)
        for channel in sorted(watcher.data[name].keys()):
            result.append(channel)
    if result:
        ievent.reply(' '.join(result))
    else:
        ievent.reply('no watchers running')


cmnds.add('ul', handle_eta, ['USER'])
cmnds.add('ul', handle_eta, ['USER'])
cmnds.add('ul-logout', handle_eta_logout, ['USER'])
cmnds.add('ul-login', handle_eta_login, ['USER'])
cmnds.add('ul-eta', handle_eta_eta, ['USER'])
cmnds.add('eta', handle_eta_eta, ['USER'])
#cmnds.add('ul-lseta', handle_eta_lseta, ['USER'])
cmnds.add('ul-subeta', handle_eta_subeta, ['USER'])
cmnds.add('ul-unsubeta', handle_eta_unsubeta, ['USER'])
cmnds.add('ul-subopen', handle_eta_subopen, ['USER'])
cmnds.add('ul-unsubopen', handle_eta_unsubopen, ['USER'])
cmnds.add('ul-subscribe', handle_eta_subeta, ['USER'])
cmnds.add('ul-unsubscribe', handle_eta_unsubeta, ['USER'])
cmnds.add('ul-lssub', handle_eta_lssub, ['ULADM'])
#cmnds.add('ul-setname', handle_eta_setname, ['USER'])
cmnds.add('eta', handle_eta, ['USER'])
examples.add('eta', 'list all user that have logged in on the mirror.', 'eta')

cmnds.add('eta-watch-start', handle_eta_watch_start, 'ULADM')
cmnds.add('eta-watch-stop',  handle_eta_watch_stop, 'ULADM')
cmnds.add('eta-watch-list',  handle_eta_watch_list, 'ULADM')

