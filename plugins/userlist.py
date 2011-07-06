# -*- coding: utf-8 -*-
# jsb.plugs.common/userlist.py
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
from jsb.lib.threadloop import TimedLoop

from jsb.lib.persist import PlugPersist

## basic imports

import re, random
import os, time, datetime
import logging
import uuid


cfg = PersistConfig()

# CONFIG SECTION #######################################################################

logindelta = 30
timeoutdelta = 600

usermap = eval(open('%s/usermap' % cfg.get('datadir')).read())

# load i18n for messages ;)

messagefile = '%s/userlist_messages' % cfg.get('datadir')

if os.path.exists(messagefile):
    #eval(open(messagefile).read())
    foo = "54"
else:
    foo = "42"

cfg.define('watcher-interval', 5)
cfg.define('watcher-enabled', 0)
cfg.define('eta-timeout', 72000)

cfg.define('userpath', '/home/c-beam/users')
cfg.define('tocendir', '/home/c-beam/usermap')

cfg.define('logindelta', 30)
cfg.define('timeoutdelta', 600)

## defines

RE_ETA = re.compile(r'ETA (?P<item>\([^\)]+\)|\[[^\]]+\]|\w+)(?P<mod>\+\+|--)( |$)')

weekdays = ['MO', 'DI', 'MI', 'DO', 'FR', 'SA', 'SO']

##

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
    elif ievent.hostname.startswith('c-base/crew/'):
        return ievent.hostname[12:]
    elif ievent.hostname.startswith('pdpc/supporter/professional/'):
        return ievent.hostname[28:]
    elif ievent.auth.endswith('@shell.c-base.org'):
        return ievent.auth[1:-17]
    else:
        return 0

class EtaItem(PlugPersist):
     def __init__(self, name, default={}):
         PlugPersist.__init__(self, name)
         self.data.name = name
         self.data.etas = self.data.etas or {}
         self.data.etatimestamps = self.data.etatimestamps or {}
         self.data.etasubs = self.data.etasubs or []
         self.data.opensubs = self.data.opensubs or []
         self.data.arrivesubs = self.data.arrivesubs or []

etaitem = EtaItem('eta')

class UserlistError(Exception): pass

class UserlistWatcher(TimedLoop):
    lastcount = -1
    lasteta = -1
    lastuserlist = []
    oldday = weekdays[datetime.datetime.now().weekday()]

    def handle(self):
        if not cfg.get('watcher-enabled'):
            raise UserlistError('watcher not enabled, use "!%s-cfg watcher-enabled 1" to enable' % os.path.basename(__file__)[:-3])
        print "fleet: %s - %s" % (str(fleet), str(fleet.list())) #"fleet.byname(%s)" % self.name
        bot = 0
        try: bot = fleet.byname(self.name)
        except: pass #print "fleet: %s" % str(fleet) #"fleet.byname(%s)" % self.name

        bot.connectok.wait()

        # LTE conversion to ETA
        day = weekdays[datetime.datetime.now().weekday()]
        if day != self.oldday:
            self.oldday = day
            dayitem = LteItem(day)
            # convert LTEs to ETAs for current day
            for user in dayitem.data.ltes.keys():
                seteta(user, dayitem.data.ltes[user][0])
                if bot and bot.type == "sxmpp":
                    for etasub in etaitem.data.etasubs:
                        bot.say(etasub, 'ETA %s %s' % (user, dayitem.data.ltes[user]))
                del dayitem.data.ltes[user]
            # clear LTEs for current day
            dayitem.data.ltes = {}
            dayitem.save()   
        try:
            users = userlist()
            usercount = len(users)
            if usercount != self.lastcount or self.lasteta != len(etaitem.data.etas):
                if self.lastcount == 0 and usercount > 0:
                    if bot and bot.type == "sxmpp":
                        for opensub in etaitem.data.opensubs:
                            bot.say(opensub, 'c3pO is awake')
                    else:
                        logging.error("bot undefined or not xmpp")

                self.lastcount = usercount
                self.lasteta = len(etaitem.data.etas)

                logging.debug("Usercount: %s" % usercount)
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
                    for user in users:
                        if user not in self.lastuserlist and not user.endswith('.logout'):
                            newusers.append(user)
                    if len(newusers) > 0:
                        logging.info('newusers: %s' % ", ".join(newusers))
                        if bot and bot.type == "sxmpp":
                            for arrivesub in etaitem.data.arrivesubs:
                                #tell subscribers who has just arrived
                                logging.info('boarding: %s -> %s' % (", ".join(newusers), arrivesub))
                                #bot.say(arrivesub, 'now boarding: %s' % ", ".join(newusers))
                        else:
                                logging.info('bot undefined or not xmpp')
                    self.lastuserlist = userlist()
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

            # remove expired users
            now = int(datetime.datetime.now().strftime("%Y%m%d%H%M%S"))
            for user in users:
                userfile = "%s/%s" % (cfg.get('userpath'), user)
                timestamps = eval(open(userfile).read())
                if timestamps[1] - now < 0:
                    os.remove(userfile)

        except UserlistError:
            logging.error("watcher error")
            pass
        except KeyError:
            logging.error("watcher error")
            pass
       
        time.sleep(cfg.get('watcher-interval'))
  
    def announce(self, status, show):
        logging.info('announce(%s, %s)' % (status, show))
        print 'announce(%s, %s)' % (status, show)
        if not self.running or not cfg.get('watcher-enabled'):
            return
        for name in fleet.list():
            bot = 0
            try: bot = fleet.byname(self.name)
            except: pass
            if bot and bot.type == "sxmpp":
                logging.info('%s[%s].setstatus(%s, %s)' % (bot.name, bot.type, status, show))
                bot.setstatus(status, show)

#watcher = ''
watcher = UserlistWatcher('default-sxmpp', cfg.get('watcher-interval'))

#watcher = UserlistWatcher()
#if not watcher.data:
#    watcher = UserlistWatcher()

def init():
    watcher.start()
    return 1 
#    if cfg.get('watcher-enabled'):
#        watcher = UserlistWatcher('ulwatcher', 5)
#        watcher.start()
#    return 1

def shutdown():
    #if watcher.running:
    watcher.stop()
    return 1

def userlist():
    return os.listdir(cfg.get('userpath'))

## userlist command

def handle_userlist(bot, ievent):
    """list all user that have logged in on the mirror."""
    users = userlist()
    reply = ''
    if len(users) > 0 or len(etaitem.data.etas) > 0:
        if len(users) > 0:
            ievent.reply('an bord: ' + ', '.join(users))
        if len(etaitem.data.etas) > 0:
            etalist = []
            for key in etaitem.data.etas.keys():
                etalist += ['%s [%s]' % (key, etaitem.data.etas[key])]
            ievent.reply('ETA: ' + ', '.join(etalist))
            #reply += 'ETA: ' + ', '.join(etalist) + '\n'
    else:
        ievent.reply("es ist derceit niemand angemeldet.")

def handle_userlist_login(bot, ievent):
    user = getuser(ievent)
    if not user: return ievent.reply('ich kenne deinen nickname noch nicht, bitte contact mit smile aufnehmen.')
    try:
        userfile = '%s/%s' % (cfg.get('userpath'), user)
#        timestamps = eval(open(userfile).read())
#        if timestamps[0] - now > 0:
        logints = datetime.datetime.now() + datetime.timedelta(seconds=logindelta)
        timeoutts = datetime.datetime.now() + datetime.timedelta(minutes=timeoutdelta)
        expire = [int(logints.strftime("%Y%m%d%H%M%S")), int(timeoutts.strftime("%Y%m%d%H%M%S"))]
        f = open(userfile, 'w')
        f.write(str(expire))
        ievent.reply('hallo %s, willkommen auf der c-base.' % user)
            #ievent.reply('du konntest nicht manuell angemeldet werden, ich weiss nicht warum. bitte contact mit smile aufnehmen.')
    except UserlistError, e:
        ievent.reply(str(s))

def handle_userlist_logout(bot, ievent):
    user = getuser(ievent)
    if not user: return ievent.reply('ich kenne deinen nickname noch nicht, bitte contact mit smile aufnehmen.')
    try:
        if os.path.exists('%s/%s' % (cfg.get('userpath'), user)):
            result = os.remove('%s/%s' % (cfg.get('userpath'), user))
            ievent.reply('danke, daC du dich abgemeldet hast %s.' % user)
        else:
            ievent.reply('du c_einst nicht angemeldet zu sein %s.' % user)
    except UserlistError, e:
        ievent.reply(str(s))

def handle_userlist_subeta(bot, ievent):
    try:
        if ievent.channel not in etaitem.data.etasubs:
            etaitem.data.etasubs.append(ievent.channel)
            etaitem.save()
        ievent.reply('danke, daC du die ETA notificationen subscribiert hast.')
    except UserlistError, e:
        ievent.reply(str(s))

def handle_userlist_unsubeta(bot, ievent):
    try:
        if ievent.channel in etaitem.data.etasubs:
            logging.info('remove %s from %s' % (ievent.channel, str(etaitem.data.etasubs)))
            etaitem.data.etasubs.remove(ievent.channel)
            etaitem.save()
        ievent.reply('du wirst erfolgreich von den ETA notificationen entsubscribiert worden sein.')
    except UserlistError, e:
        ievent.reply(str(s))
   
def handle_userlist_subopen(bot, ievent):
    try:
        if ievent.channel not in etaitem.data.opensubs:
            etaitem.data.opensubs.append(ievent.channel)
            etaitem.save()
        ievent.reply('thank you for your opening notification subscription')
    except UserlistError, e:
        ievent.reply(str(s))

def handle_userlist_subarrive(bot, ievent):
    try:
        if ievent.channel not in etaitem.data.arrivesubs:
            etaitem.data.arrivesubs.append(ievent.channel)
            etaitem.save()
        ievent.reply('thank you for your arrival notification subscription')
    except UserlistError, e:
        ievent.reply(str(s))

def handle_userlist_unsubarrive(bot, ievent):
    try:
        if ievent.channel in etaitem.data.arrivesubs:
            logging.info('remove %s from %s' % (ievent.channel, str(etaitem.data.arrivesubs)))
            etaitem.data.arrivesubs.remove(ievent.channel)
            etaitem.save()
        ievent.reply('you have been unsubscribed from boarding notifications')
    except UserlistError, e:
        ievent.reply(str(s))

def handle_userlist_unsubopen(bot, ievent):
    try:
        if ievent.channel in etaitem.data.opensubs:
            logging.info('remove %s from %s' % (ievent.channel, str(etaitem.data.opensubs)))
            etaitem.data.opensubs.remove(ievent.channel)
            etaitem.save()
        ievent.reply('you have been unsubscribed from opening notifications')
    except UserlistError, e:
        ievent.reply(str(s))
    
    
def handle_userlist_lssub(bot, ievent):
    try:
        ievent.reply('ATT-Subbscribers: %s\nOpening Subscribers: %s\nETA-Subscribers: %s' % (str(etaitem.data.subscribers), str(etaitem.data.arrivesubs), str(etaitem.data.etasubs)))
    except UserlistError, e:
        ievent.reply(str(s))

def handle_userlist_lseta(bot, ievent):
    try:
        if len(etaitem.data.etas) > 0:
            etalist = []
            for key in etaitem.data.etas.keys():
                etalist += ['%s [%s]' % (key, etaitem.data.etas[key])]
            ievent.reply('ETA: %s' % ', '.join(etalist))
    except UserlistError, e:
        ievent.reply(str(s))

def seteta(user, eta):
    if eta == '0':
        del etaitem.data.etas[user]
    else:
        etaitem.data.etas[user] = eta
        etaitem.data.etatimestamps[user] = time.time() + cfg.get('eta-timeout')
    etaitem.save()


def handle_userlist_eta(bot, ievent):

    user = getuser(ievent)
    if not user: return ievent.reply('ich kenne deinen nickname noch nicht, bitte contact mit smile aufnehmen.')

    eta = 0
    if ievent.args[0].upper() in weekdays:
        return handle_lte(bot, ievent)
    if ievent.args[0] in ('gleich', 'bald'):
        etaval = datetime.datetime.now() + datetime.timedelta(minutes=30)
        eta = int(etaval.strftime("%H%M"))
    elif ievent.args[0].startswith('+'):
        foo = int(ievent.args[0][1:])
        etaval = datetime.datetime.now() + datetime.timedelta(minutes=foo)
        eta = etaval.strftime("%H%M")
    else:
        eta = ievent.rest

    eta = re.sub(r'(\d\d):(\d\d)',r'\1\2',eta)
    print "ETA: %s" % eta
    logging.info("ETA: %s" % eta)
        
    seteta(user, eta)

    try:
        for etasub in etaitem.data.etasubs:
            logging.info( "sending eta %s to %s" % (eta, user))
            bot.say(etasub, 'ETA %s %s' % (user, eta))
        #ievent.reply('Set eta for %s to %d' % (user, eta))
        if eta == 0:
            ievent.reply('c_ade, daC du doch nicht kommen cannst. [ETA: %s]' % (user, eta))
        else:
            ievent.reply('danke, daC du bescheid sagst %s. [ETA: %s]' % (user, eta))
 
    except UserlistError, e:
        ievent.reply(str(s))

def handle_userlist_watch_start(bot, ievent):
    if not cfg.get('watcher-enabled'):
        ievent.reply('watcher not enabled, use "!%s-cfg watcher-enabled 1" to enable and reload the plugin' % os.path.basename(__file__)[:-3])
        return
    watcher.add(bot, ievent)
    ievent.reply('ok')

def handle_userlist_watch_stop(bot, ievent):
    if not cfg.get('watcher-enabled'):
        ievent.reply('watcher not enabled, use "!%s-cfg watcher-enabled 1" to enable and reload the plugin' % os.path.basename(__file__)[:-3])
        return
    watcher.remove(bot, ievent)
    ievent.reply('ok')

def handle_userlist_watch_list(bot, ievent):
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


cmnds.add('ul', handle_userlist, ['GUEST'])
cmnds.add('who', handle_userlist, ['GUEST'])
cmnds.add('ul-logout', handle_userlist_logout, ['GUEST'])
cmnds.add('logout', handle_userlist_logout, ['GUEST'])
cmnds.add('ul-login', handle_userlist_login, ['GUEST'])
cmnds.add('login', handle_userlist_login, ['GUEST'])
cmnds.add('ul-eta', handle_userlist_eta, ['GUEST'])
cmnds.add('eta', handle_userlist_eta, ['GUEST'])
cmnds.add('ul-subeta', handle_userlist_subeta, ['GUEST'])
cmnds.add('ul-unsubeta', handle_userlist_unsubeta, ['GUEST'])
cmnds.add('ul-subarrive', handle_userlist_subarrive, ['GUEST'])
cmnds.add('ul-subopen', handle_userlist_subopen, ['USER'])
cmnds.add('ul-unsubopen', handle_userlist_unsubopen, ['USER'])
cmnds.add('ul-unsubarrive', handle_userlist_unsubarrive, ['GUEST'])
cmnds.add('ul-subscribe', handle_userlist_subeta, ['GUEST'])
cmnds.add('ul-unsubscribe', handle_userlist_unsubeta, ['GUEST'])
cmnds.add('ul-lssub', handle_userlist_lssub, ['ULADM'])
cmnds.add('userlist', handle_userlist, ['GUEST'])

cmnds.add('userlist-watch-start', handle_userlist_watch_start, 'ULADM')
cmnds.add('userlist-watch-stop',  handle_userlist_watch_stop, 'ULADM')
cmnds.add('userlist-watch-list',  handle_userlist_watch_list, 'ULADM')

def handle_whoami(bot, ievent):
    replies = [
        'du wirst %s gewesen worden sein.',
        'du wirst %s gewesen sein.',
        'du c_einst ein clon von %s zu sein.',
        'gruCfrequencen %s.',
        'das cann eigentlich nur %s sein.',
        '%s.',
        '%s wars.',
        'deine dna weist spuren von %s auf.',
        'ich dence du bist %s.'
    ]
    user = getuser(ievent)
    if not user: return ievent.reply('ich kenne deinen nickname noch nicht, bitte contact mit smile aufnehmen.')
    return ievent.reply(random.choice(replies) % user)
    

cmnds.add('whoami', handle_whoami, ['GUEST'])

# MO 1900 2300
class LteItem(PlugPersist):
    def __init__(self, name, default={}):
         PlugPersist.__init__(self, name)
         self.data.name = name
         self.data.ltes = self.data.ltes or {}

def handle_lte(bot, ievent):
    user = getuser(ievent)
    if not user: return ievent.reply('ich kenne deinen nickname noch nicht, bitte contact mit smile aufnehmen.')
    item = LteItem(user)
    args = ievent.rest.upper().split(' ')
    lteusers = PlugPersist('lteusers')
    if not lteusers.data: lteusers.data = {}

    if len(ievent.args) == 3 or len(ievent.args) == 2:
        if args[1] == '0':
            dayitem = LteItem(args[0])
            if user in dayitem.data.ltes.keys():
                del dayitem.data.ltes[user]            
                dayitem.save()
                return ievent.reply('dancce %s, dein LTE für %s wurde entfernt.' % (user, args[0]))
            else:
                return ievent.reply('entc_uldige %s, du hattest wohl keinen ETA für %s gesetzt.' % (user, args[0]))
        if args[0] not in ('MO', 'DI', 'MI', 'DO', 'FR', 'SA', 'SO'): 
            #, 'MO', 'TU', 'WE', 'TH', 'FR', 'SA', 'SU'):
            return ievent.reply('LTE syntax: !lte MO 1900')
        item.data.ltes[args[0]] = args
        item.save()
        dayitem = LteItem(args[0])
        eta = " ".join(args[1:])
        eta = re.sub(r'(\d\d):(\d\d)',r'\1\2', eta)
        dayitem.data.ltes[user] = eta
        dayitem.save()
        lteusers.data[user] = time.time()
        lteusers.save()
        ievent.reply('dancce %s, dein LTE wurde gespeichert. [%s]' % (user, eta))

    elif len(ievent.args) == 1:
        if args[0] in ('MO', 'DI', 'MI', 'DO', 'FR', 'SA', 'SO'):
            dayitem = LteItem(args[0])
            if len(dayitem.data.ltes.keys()) > 0:
                reply = 'LTEs für %s: ' % args[0]
                for user in dayitem.data.ltes.keys():
                    reply += '%s [%s] ' % (user, dayitem.data.ltes[user])
                ievent.reply(reply)
        else:
            ievent.reply('ich cenne den tag %s nicht.' % args[0])
    elif len(ievent.args) == 0:
        reply = ''
        for day in weekdays:
            dayitem = LteItem(day)
            if len(dayitem.data.ltes.keys()) > 0:
                #reply += '%s: %s ' % (day, ', '.join(dayitem.data.ltes.keys()))
                ievent.reply('%s: %s ' % (day, ', '.join(dayitem.data.ltes.keys())))
        #ievent.reply(reply)
    else:
        ievent.reply(str(len(ievent.rest.split(' '))))

cmnds.add('lte', handle_lte, ['GUEST'])


def handle_login_tocen(bot, ievent):
    tocendir = cfg.get('tocendir')
    user = getuser(ievent)
    if not user: return ievent.reply('ich kenne deinen nickname noch nicht, bitte contact mit smile aufnehmen.')
    presencename = 'presence.c-base.org/%s' % user
    userid = uuid.uuid3(uuid.NAMESPACE_DNS, presencename.encode('utf8')).hex
    tocenfile = '%s/%s' % (tocendir, userid)
    if not os.path.exists(tocenfile):
       f = open('%s/%s' % (tocendir, userid), 'w')
       f.write(user)
       f.close()
    httpurl = "http://10.0.1.27:8080"
    return ievent.reply('%s/login/%s' % (httpurl, userid))

cmnds.add('login-tocen', handle_login_tocen, ['GUEST', 'USER'])
