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
#import jsonrpclib
from jsonrpc.proxy import ServiceProxy

cfg = PersistConfig()

# CONFIG SECTION #######################################################################

usermap = eval(open('%s/usermap' % cfg.get('datadir')).read())

# load i18n for messages ;)

messagefile = '%s/userlist_messages' % cfg.get('datadir')

messages = {}

if os.path.exists(messagefile):
    try:
        messages = eval(open(messagefile).read())
    except: logging.error('error in userlist_messages')
else:
    messages = {
        'unknown_nick': ['ich kenne deinen nickname noch nicht, bitte contact mit smile/cmile aufnehmen.'],
        'logged_in': ['an bord: [%d]'],
        'login_success': ['hallo %s, willkommen auf der c-base.', 'hallo %s, willkommen an bord!'],
        'login_remind': ['Denk daran: %s'],
        'logout_success': ['danke, daC du dich abgemeldet hast %s.', 'danke und guten heimflug %s.'],
        'no_one_there': ['derceit hat sich keine cohlenstoffeinheit bei mir angemeldet.', 'ga:hnende leere', 'an bord: keiner!'],
        'eta_set': ['danke, daC du bescheid sagst %s. [ETA: %s]'],
        'eta_removed': ['c_ade, daC du doch nicht kommen cannst %s. [ETA: %s]'],
        'lte_set': ['danke %s, dein LTE wurde gespeichert. [%s]'],
        'lte_removed': ['danke %s, ich habe dein LTE für %s entfernt.'],
        'subeta_success': ['danke, daC du die ETA notificationen subscribiert hast.'],
        'unsubeta_success': ['du wirst erfolgreich von den ETA notificationen entsubscribiert worden sein.'],
        'subopen_success': ['thank you for your opening notification subscription'],
        'subarrive_success': ['thank you for your arrival notification subscription'],
        'unsubarrive_success': ['you have been unsubscribed from boarding notifications'],
        'unsubopen_success': ['you have been unsubscribed from opening notifications'],
        'err_timeparser': ['leider connte keine verwertbare ceitangabe aus deiner eingabe extrahiert werden.'],
        'err_unknown_day': ['ich cenne den tag %s nicht.'],
        'etd_removed': ['dein ETD wurde entfernt %s. [ETD: %s]'],
        'etd_set': ['dein ETD wurde erfolgreich gespeichert %s. [ETD: %s]'],
        'no_etds': ['niemand hat ein ETD eingetragen %s.'],
        'whoami': ['du wirst %s gewesen worden sein.', 'du wirst %s gewesen sein.', 'du ähnelst einem clon von %s.', 'gruCfrequencen %s.', '%s.', '%s fummelt an c-beam.', 'deine dna weist spuren von %s auf.', 'deine moleculare structur gleicht der von %s.', 'ich dence du formst ein %s.', 'deiner mudder ihr spro:Cling, %s'],
        'vlogged_in': ['im c-base village: '],
        'vlogin_success': ['hallo %s, willkommen im c-base village!'],
        'vlogout_success': ['scho:n daC du im c-base village vorbeigeschaut hast %s.'],

    }

cfg.define('watcher-interval', 5)
cfg.define('watcher-enabled', 0)
cfg.define('eta-timeout', 120)
cfg.define('etd-timeout', 180)

cfg.define('tocendir', '/home/c-beam/usermap')

cfg.define('suppress-subs', 0)

cfg.define('use-c-beamd', 0)
cfg.define('c-beam-url', 'http://127.0.0.1:4254')

cfg.define('set-xmpp-presence', 0)

cfg.define('achievement-channel', '#c-base-bots')
cfg.define('achievement-bot', 'default-irc')

## defines

RE_ETA = re.compile(r'ETA (?P<item>\([^\)]+\)|\[[^\]]+\]|\w+)(?P<mod>\+\+|--)( |$)')

weekdays = ['MO', 'DI', 'MI', 'DO', 'FR', 'SA', 'SO']

nextday = ['tomorrow', 'morgen']

##
#jsonrpclib.config.version = 1.0
#server = jsonrpclib.Server(cfg.get('c-beam-url'))
server = ServiceProxy(cfg.get('c-beam-url'))

def getuser2(user):
    if user in usermap:
        return usermap[user]
    elif user.find('@c-base.org') > -1:
        return user[:-11]
    elif user.endswith('@shell.c-base.org'):
        return user[1:-17]
    elif user.endswith('@176.74.60.210'):
        return user[1:-14]
    elif user.startswith('c-base/crew/'):
        return user[12:]
    elif user.startswith('pdpc/supporter/professional/'):
        return user[28:]
    else:
        return user

def getuser(ievent):
    if ievent.channel in usermap:
        return usermap[ievent.channel]
    elif ievent.fromm and ievent.fromm in usermap:
        return usermap[ievent.fromm]
    elif ievent.nick and ievent.nick in usermap:
        return usermap[ievent.nick]
    elif ievent.ruserhost in usermap:
        return usermap[ievent.ruserhost]
    elif ievent.auth.endswith('@shell.c-base.org'):
        return ievent.auth[:-17]
    elif ievent.auth.endswith('@176.74.60.210'):
        return ievent.auth[1:-14]
    elif ievent.channel.find('@c-base.org') > -1:
        return ievent.channel[:-11]
    elif ievent.fromm and ievent.fromm.find('c-base.org') > -1:
        return ievent.fromm[:-10]
    elif ievent.hostname and ievent.hostname.startswith('c-base/crew/'):
        return ievent.hostname[12:]
    elif ievent.hostname and ievent.hostname.startswith('pdpc/supporter/professional/'):
        return ievent.hostname[28:]
    elif ievent.hostname and ievent.ruserhost.find('@gateway/shell/c-base') > -1:
        return ievent.ruserhost[:ievent.ruserhost.find('@')]
    else:
        return 0

class EtaItem(PlugPersist):
     def __init__(self, name, default={}):
         PlugPersist.__init__(self, name)
         self.data.name = name
         self.data.etas = self.data.etas or {}
         self.data.etds = self.data.etds or {}
         self.data.etatimestamps = self.data.etatimestamps or {}
         self.data.etdtimestamps = self.data.etdtimestamps or {}
         self.data.etasubs = self.data.etasubs or []
         self.data.opensubs = self.data.opensubs or []
         self.data.arrivesubs = self.data.arrivesubs or []
         self.data.logintimeouts = self.data.logintimeouts or {}

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
        logging.info("fleet: %s - %s" % (str(fleet), str(fleet.list())))
        bot = 0
        try: bot = fleet.byname(self.name)
        except: pass #print "fleet: %s" % str(fleet) #"fleet.byname(%s)" % self.name

        if bot != None:
            bot.connectok.wait()

        # LTE conversion to ETA
        day = weekdays[datetime.datetime.now().weekday()]
        if day != self.oldday:
            self.oldday = day
            dayitem = LteItem(day)
            # convert LTEs to ETAs for current day
            for user in dayitem.data.ltes.keys():
                server.seteta(user, dayitem.data.ltes[user])
                if bot and bot.type == "sxmpp" and cfg.get('suppress-subs') == 0:
                    for etasub in etaitem.data.etasubs:
                        bot.say(etasub, 'ETA %s %s' % (user, dayitem.data.ltes[user]))
                del dayitem.data.ltes[user]
            # clear LTEs for current day
            dayitem.data.ltes = {}
            dayitem.save()   
        
        whoresult = server.who()['result']
            
        # check if new ETAs have been added
        newetas = server.newetas()['result']
        if len(newetas) > 0:
            for etasub in etaitem.data.etasubs:
                etalist = []
                for key in sorted(newetas.keys()):
                    if getuser2(etasub) == key:
                        print "skip notifying yourself"
                    else:
                        etalist += ['%s [%s]' % (key, newetas[key])]
                if bot and bot.type == "sxmpp" and len(etalist) > 0:
                    bot.say(etasub, 'ETA: ' + ', '.join(etalist))

        # check for new achievements
        achievements = server.achievements()
        if len(achievements) > 0:
            for user in achievements.keys():
                if achievements[user] == 'ETA':
                    print "%s++" % user
                    tmpbot = 0
                    try: 
                        tmpbot = fleet.byname(cfg.get('achievement-bot'))
                        tmpbot.say(cfg.get('achievement-channel'), '%s++' % user)
                    except: pass

        # check if new users have arrived
        arrivals = server.arrivals()['result']
        if len(arrivals) > 0:
            for arrivesub in etaitem.data.arrivesubs:
                arrivelist = ', '.join(sorted(arrivals.keys()))
                if bot and bot.type == "sxmpp":
                    bot.say(arrivesub, 'Now boarding: ' + arrivelist)
        
        # activities
	activities = server.activities()['result']
        if len(activities) > 0:
            print activities

        usercount = len(whoresult['available'])
        if self.lastcount == 0 and usercount > 0:
            if bot and bot.type == "sxmpp":
                for opensub in etaitem.data.opensubs:
                    #bot.say(opensub, 'c3pO is awake')
                    print "FUUUUUUUUUUUU"
            else:
                logging.error("bot undefined or not xmpp")

        self.lastcount = usercount
 
        if (cfg.get('set-xmpp-presence') > 0):
            if len(whoresult['available']) > 0:
                self.announce('open', 'chat')
            elif len(whoresult['eta']) > 0:
                self.announce('incoming', 'dnd')
            else:
                self.announce('closed', 'xa')

        time.sleep(cfg.get('watcher-interval'))
  
    def announce(self, status, show):
        logging.info('announce(%s, %s)' % (status, show))
        #print 'announce(%s, %s)' % (status, show)
        if not self.running or not cfg.get('watcher-enabled'):
            return
        for name in fleet.list():
            bot = 0
            try: bot = fleet.byname(name)
            except: pass
            if bot and bot.type == "sxmpp":
                logging.warn('%s[%s].setstatus(%s, %s)' % (bot.name, bot.type, status, show))
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

def getmessage(msg_name):
    msg = random.choice(messages[msg_name])
    if msg == "":
        msg = "die sprachdatei c_eint defect zu sein. hilfe. 0010100100000000000"
    return msg

## userlist command

def handle_userlist(bot, ievent):
    """list all user that have logged in."""
    user = getuser(ievent)
    if not user: return ievent.reply(getmessage('unknown_nick'))
    if ievent.channel == "#hackerspaces": return
    whoresult = server.who()['result']
    if len(whoresult['available']) > 0 or len(whoresult['eta']) > 0:
        result = []
        if len(whoresult['available']) > 0:
            
            for n, user in enumerate(whoresult['available']):
                if whoresult['lastlocation'].has_key(user):
                    whoresult['available'][n] = '%s (%s)' % (user, whoresult['lastlocation'][user])
            result.append(getmessage('logged_in') % len(whoresult['available']) + ', '.join(whoresult['available']))
            #ievent.reply(getmessage('logged_in') + ', '.join(whoresult['available']))
        if len(whoresult['eta']) > 0:
            etalist = []
            for key in sorted(whoresult['eta'].keys()):
               etalist += ['%s [%s]' % (key, whoresult['eta'][key])]
            result.append('ETA: ' + ', '.join(etalist))
            #ievent.reply('ETA: ' + ', '.join(etalist))
        if len(whoresult['etd']) > 0:
            etalist = []
            for key in sorted(whoresult['etd'].keys()):
               etalist += ['%s [%s]' % (key, whoresult['etd'][key])]
            result.append('ETD: ' + ', '.join(etalist))
        if ievent.channel == "#c-base":
            #bot.say(" | ".join(result))
            ievent.reply(" | ".join(result))
        else:
            ievent.reply(" | ".join(result))
    else:
        if ievent.channel == "#c-base":
            #bot.say(getmessage('no_one_there'))
            ievent.reply(getmessage('no_one_there'))
        else:
            ievent.reply(getmessage('no_one_there'))

def handle_userlist_login(bot, ievent):
    user = getuser(ievent)
    if not user: return ievent.reply(getmessage('unknown_nick'))
    
    result = server.login(user)['result']
    ievent.reply(getmessage('login_success') % user)
    if result != "aye" and result != "":
        ievent.reply(getmessage('login_remind') % reminder)

cmnds.add('ul-login', handle_userlist_login, ['GUEST', 'USER'])
cmnds.add('login', handle_userlist_login, ['GUEST', 'USER'])
cmnds.add('da', handle_userlist_login, ['GUEST', 'USER'])

def handle_userlist_slogin(bot, ievent):
    user = getuser(ievent)
    if not user: return ievent.reply(getmessage('unknown_nick'))
    
    result = server.slogin(user)['result']
    ievent.reply(getmessage('login_success') % user)

cmnds.add('slogin', handle_userlist_slogin, ['GUEST', 'USER'])

def handle_userlist_logout(bot, ievent):
    user = getuser(ievent)
    if not user: return ievent.reply(getmessage('unknown_nick'))
    server.logout(user)['result']
    ievent.reply(getmessage('logout_success') % user)

cmnds.add('ul-logout', handle_userlist_logout, ['GUEST', 'USER'])
cmnds.add('logout', handle_userlist_logout, ['GUEST', 'USER'])
cmnds.add('weg', handle_userlist_logout, ['GUEST', 'USER'])

def handle_userlist_slogout(bot, ievent):
    user = getuser(ievent)
    if not user: return ievent.reply(getmessage('unknown_nick'))
    result = server.slogout(user)['result']
    ievent.reply(getmessage('logout_success') % user)

cmnds.add('slogout', handle_userlist_slogout, ['GUEST', 'USER'])

def handle_userlist_subeta(bot, ievent):
    try:
        if ievent.channel not in etaitem.data.etasubs:
            etaitem.data.etasubs.append(ievent.channel)
            etaitem.save()
        ievent.reply(getmessage('subeta_success'))
    except UserlistError, e:
        ievent.reply(str(s))

def handle_userlist_unsubeta(bot, ievent):
    try:
        if ievent.channel in etaitem.data.etasubs:
            logging.info('remove %s from %s' % (ievent.channel, str(etaitem.data.etasubs)))
            etaitem.data.etasubs.remove(ievent.channel)
            etaitem.save()
        ievent.reply(getmessage('unsubeta_success'))
    except UserlistError, e:
        ievent.reply(str(s))
   
def handle_userlist_subopen(bot, ievent):
    try:
        if ievent.channel not in etaitem.data.opensubs:
            etaitem.data.opensubs.append(ievent.channel)
            etaitem.save()
        ievent.reply(getmessage('subopen_success'))
    except UserlistError, e:
        ievent.reply(str(s))

def handle_userlist_subarrive(bot, ievent):
    try:
        if ievent.channel not in etaitem.data.arrivesubs:
            etaitem.data.arrivesubs.append(ievent.channel)
            etaitem.save()
        ievent.reply(getmessage('subarrive_success'))
    except UserlistError, e:
        ievent.reply(str(s))

def handle_userlist_unsubarrive(bot, ievent):
    try:
        if ievent.channel in etaitem.data.arrivesubs:
            logging.info('remove %s from %s' % (ievent.channel, str(etaitem.data.arrivesubs)))
            etaitem.data.arrivesubs.remove(ievent.channel)
            etaitem.save()
        ievent.reply(getmessage('unsubarrive_success'))
    except UserlistError, e:
        ievent.reply(str(s))

def handle_userlist_unsubopen(bot, ievent):
    try:
        if ievent.channel in etaitem.data.opensubs:
            logging.info('remove %s from %s' % (ievent.channel, str(etaitem.data.opensubs)))
            etaitem.data.opensubs.remove(ievent.channel)
            etaitem.save()
        ievent.reply(getmessage('unsubopen_success'))
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

def extract_eta(text):
    m = re.match(r'^.*?(\d\d\d\d).*', text)
    if m:
        return m.group(1)
    else:
        return "9999"

def handle_userlist_eta(bot, ievent):
    user = getuser(ievent)
    if not user: return ievent.reply(getmessage('unknown_nick'))

    eta = ievent.rest

    # return userlist if no arguments are provided
    if len(ievent.args) == 0:
        return handle_userlist(bot, ievent)

    # if the first argument is a weekday, delegate to LTE
    if ievent.args[0].upper() in weekdays:
        return handle_lte(bot, ievent)

    result = server.eta(user, eta)['result']
    print result
    ievent.reply(getmessage(result) % (user, eta))

def handle_userlist_stealthmode(bot, ievent):
    user = getuser(ievent)
    if not user: return ievent.reply(getmessage('unknown_nick'))

    if len(ievent.args) == 0:
        result = server.get_stealthmode(user)['result']
        return ievent.reply(result)

    stealthtime = int(ievent.rest)
    print "stealhtmode %s %d" % (user, stealthtime)
    result = server.set_stealthmode(user, stealthtime)['result']
    print result
    #ievent.reply(getmessage(result) % (user, eta))
    ievent.reply(result)

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


cmnds.add('ul-eta', handle_userlist_eta, ['GUEST', 'USER'])
cmnds.add('eta', handle_userlist_eta, ['GUEST', 'USER'])
cmnds.add('ul-subeta', handle_userlist_subeta, ['GUEST', 'USER'])
cmnds.add('eta-sub', handle_userlist_subeta, ['GUEST', 'USER'])
cmnds.add('ul-unsubeta', handle_userlist_unsubeta, ['GUEST', 'USER'])
cmnds.add('ul-subarrive', handle_userlist_subarrive, ['GUEST', 'USER'])
cmnds.add('ul-subopen', handle_userlist_subopen, ['USER'])
cmnds.add('ul-unsubopen', handle_userlist_unsubopen, ['USER'])
cmnds.add('ul-unsubarrive', handle_userlist_unsubarrive, ['GUEST', 'USER'])
cmnds.add('ul-subscribe', handle_userlist_subeta, ['GUEST', 'USER'])
cmnds.add('ul-unsubscribe', handle_userlist_unsubeta, ['GUEST', 'USER'])
cmnds.add('ul-lssub', handle_userlist_lssub, ['ULADM', 'OPER'])
cmnds.add('userlist', handle_userlist, ['GUEST', 'USER'])
cmnds.add('stealthmode', handle_userlist_stealthmode, ['GUEST', 'USER'])

cmnds.add('userlist-watch-start', handle_userlist_watch_start, 'ULADM')
cmnds.add('userlist-watch-stop',  handle_userlist_watch_stop, 'ULADM')
cmnds.add('userlist-watch-list',  handle_userlist_watch_list, 'ULADM')

def handle_whoami(bot, ievent):
    user = getuser(ievent)
    if not user: return ievent.reply(getmessage('unknown_nick'))
    return ievent.reply(getmessage('whoami') % user)
    

cmnds.add('whoami', handle_whoami, ['GUEST', 'USER'])

# MO 1900 2300
class LteItem(PlugPersist):
    def __init__(self, name, default={}):
         PlugPersist.__init__(self, name)
         self.data.name = name
         self.data.ltes = self.data.ltes or {}

def handle_lte(bot, ievent):
    user = getuser(ievent)
    if not user: return ievent.reply(getmessage('unknown_nick'))
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
            return ievent.reply(getmessage('lte_removed') % (user, args[0]))
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
        ievent.reply(getmessage('lte_set') % (user, eta))

    elif len(ievent.args) == 1:
        if args[0] in ('MO', 'DI', 'MI', 'DO', 'FR', 'SA', 'SO'):
            dayitem = LteItem(args[0])
            if len(dayitem.data.ltes.keys()) > 0:
                reply = 'LTEs für %s: ' % args[0]
                for user in dayitem.data.ltes.keys():
                    reply += '%s [%s] ' % (user, dayitem.data.ltes[user])
                ievent.reply(reply)
        else:
            ievent.reply(getmessage('err_unknown_day') % args[0])
    elif len(ievent.args) == 0:
        reply = []
        for day in weekdays:
            dayitem = LteItem(day)
            if len(dayitem.data.ltes.keys()) > 0:
                #reply += '%s: %s ' % (day, ', '.join(dayitem.data.ltes.keys()))
                reply.append('%s: %s ' % (day, ', '.join(dayitem.data.ltes.keys())))
        ievent.reply(" | ".join(reply))
    else:
        ievent.reply(str(len(ievent.rest.split(' '))))

cmnds.add('lte', handle_lte, ['GUEST', 'USER'])


def handle_login_tocen(bot, ievent):
    tocendir = cfg.get('tocendir')
    user = getuser(ievent)
    if not user: return ievent.reply(getmessage('unknown_nick'))
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

def handle_userlist_etd(bot, ievent):
    user = getuser(ievent)
    if not user: return ievent.reply(getmessage('unknown_nick'))

    etd = ievent.rest

    # return userlist if no arguments are provided
    if len(ievent.args) == 0:
        return handle_userlist(bot, ievent)

    result = server.etd(user, etd)['result']
    ievent.reply(getmessage(result) % (user, etd))

cmnds.add('etd', handle_userlist_etd, ['GUEST', 'USER'])

def handle_userlist_settimeout(bot, ievent):
    user = getuser(ievent)
    if not user: return ievent.reply(getmessage('unknown_nick'))

    if len(ievent.args) == 0:
        return ievent.missing('timeout')
    elif len(ievent.args) == 1:
        timeout = int(ievent.args[0])
    else:
        return ievent.reply('!login-timeout <timeout>')

    try:
        etaitem.data.logintimeouts[user] = timeout
        etaitem.save()
#        ievent.reply(getmessage('subarrive_success'))

    except UserlistError, e:
        ievent.reply(str(s))

cmnds.add('login-timeout', handle_userlist_settimeout, ['GUEST', 'USER'])


def handle_userlist_veta(bot, ievent):
    user = getuser(ievent)
    if not user: return ievent.reply(getmessage('unknown_nick'))

    eta = ievent.rest

    # return userlist if no arguments are provided
    if len(ievent.args) == 0:
        return handle_userlist(bot, ievent)

    result = server.veta(user, eta)
    ievent.reply(getmessage(result) % (user, eta))

cmnds.add('veta', handle_userlist_veta, ['GUEST', 'USER'])

def handle_userlist_vlogin(bot, ievent):
    user = getuser(ievent)
    if not user: return ievent.reply(getmessage('unknown_nick'))
    
    result = server.vlogin(user)
    ievent.reply(getmessage('vlogin_success') % user)

cmnds.add('vlogin', handle_userlist_vlogin, ['GUEST', 'USER'])

def handle_userlist_vlogout(bot, ievent):
    user = getuser(ievent)
    if not user: return ievent.reply(getmessage('unknown_nick'))
    server.vlogout(user)
    ievent.reply(getmessage('vlogout_success') % user)

cmnds.add('vlogout', handle_userlist_vlogout, ['GUEST', 'USER'])

def handle_vuserlist(bot, ievent):
    """list all user that have logged in."""
    whoresult = server.who()
    reply = ""
    if len(whoresult['available']) > 0 or len(whoresult['eta']) > 0 or len(whoresult['vavailable']) > 0 or len(whoresult['veta']) > 0:
        if len(whoresult['available']) > 0:
            reply += getmessage('logged_in') + ', '.join(whoresult['available']) + " | "
        if len(whoresult['vavailable']) > 0:
            reply += getmessage('vlogged_in') + ', '.join(whoresult['vavailable']) + " | "
        if len(whoresult['eta']) > 0:
            etalist = []
            for key in sorted(whoresult['eta'].keys()):
               etalist += ['%s [%s]' % (key, whoresult['eta'][key])]
            reply += 'ETA: ' + ', '.join(etalist) + " | "
        if len(whoresult['veta']) > 0:
            vetalist = []
            for key in sorted(whoresult['veta'].keys()):
               vetalist += ['%s [%s]' % (key, whoresult['veta'][key])]
            reply += 'villageETA: ' + ', '.join(vetalist)
        if reply.endswith(" | "):
            reply = reply[:-3]
        ievent.reply(reply)
    else:
        ievent.reply(getmessage('no_one_there'))

cmnds.add('ul', handle_userlist, ['GUEST', 'USER'])
cmnds.add('who', handle_userlist, ['GUEST', 'USER'])

def handle_ddate(bot, ievent):
    if ievent.rest == '+%.':
        msg = server.fnord()['result']
    else:
        msg = server.ddate()['result']
    if ievent.channel == '#c-base':
        bot.say('#c-base', msg)
    else:
        ievent.reply(msg)

cmnds.add('ddate', handle_ddate, ['GUEST', 'USER', 'OPER'])

def handle_sdate(bot, ievent):
    stream = os.popen("sdate")
    result = stream.readline().rstrip()
    ievent.reply(result)

cmnds.add('sdate', handle_sdate, ['GUEST', 'USER', 'OPER'])

def handle_remindme(bot, ievent):
    user = getuser(ievent)
    server.remind(user, ievent.rest)
    ievent.reply("aye")
    
cmnds.add('remindme', handle_remindme, ['GUEST', 'USER', 'OPER'])

def handle_bluewall(bot, ievent):
    user = getuser(ievent)
    if not user: return ievent.reply(getmessage('unknown_nick'))
    server.bluewall()
    ievent.reply("aye")
    
cmnds.add('bluewall', handle_bluewall, ['GUEST', 'USER', 'OPER'])

def handle_darkwall(bot, ievent):
    user = getuser(ievent)
    if not user: return ievent.reply(getmessage('unknown_nick'))
    server.darkwall()
    ievent.reply("aye")
    
cmnds.add('darkwall', handle_darkwall, ['GUEST', 'USER', 'OPER'])
