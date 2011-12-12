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
from jsb.lib.persiststate import UserState
from jsb.utils.lazydict import LazyDict


## basic imports

import logging
import re
import random
from jsb.lib.persiststate import PlugState

## defines

RE_STRONGPRONOUN = re.compile(r'\b(man|bernd)\b', re.IGNORECASE)
#RE_WEAKPRONOUN = re.compile(r'\b(jemand|irgendwer|einer|wer)\b', re.IGNORECASE)
RE_WEAKPRONOUN = re.compile(r'\b(jemand|irgendwer|einer|wer|deine mudder|deine mudda)\b', re.IGNORECASE)
RE_CONJUNCTIVE = re.compile(r'\b(sollte|soLte|m\xfcsste|muesste|mu:sste|mu:Cte|k\xf6nnte|koennte|co:nnte|co:Nte|ko:nnte|ko:Nte|h\xe4tte|haette|ha:tte|ha:Te|br\xe4uchte|braeuchte|bra:uchte|wuerde|wu:rde|w\xfcrde)\b', re.IGNORECASE)
RE_ADDONS = re.compile(r'\b(mal)\b', re.IGNORECASE)
RE_QUESTION = re.compile(r'\?', re.IGNORECASE)
RE_HELP = re.compile(r'(helfen|erklaeren|erkl\xe4ren|erkla:ren)\b', re.IGNORECASE)
RE_STRIP_QUOTE = re.compile(r'("|<quote>).*?("|</quote>)', re.IGNORECASE)

initdone = False

cfg = PersistConfig()
usermap = eval(open('%s/usermap' % cfg.get('datadir')).read())

## Hubel class

class Hubel(LazyDict):
    def __init__(self, rating=0):
        self.rating = rating
    pass

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
    
class HubelList(UserState):

    def __init__(self, name, *args, **kwargs):
        UserState.__init__(self, name, "hubel", *args, **kwargs)
        if self.data.list: self.data.list = [LazyDict(x) for x in self.data.list]
        else: self.data.list = []
        self.name = name

    def add(self, txt):
        """ add a hubel """
        hubel = Hubel()
        hubel.txt = txt
        self.data.list.append(hubel)
        self.save()
        return len(self.data.list)

    def delete(self, indexnr):
        """ delete a hubel. """
        del self.data.list[indexnr-1]
        self.save()
        return self

    def clear(self):
        """ clear the hubel list. """
        self.data.list = []
        self.save()
        return self

    def increase(self):
        return self
    def decrease(self):
        return self

def init():
    global state
    global initdone
    state = PlugState()
    state.define('hubel', {})
    initdone = True
    return 1

def checkhubel(text):
    stripped = re.sub(RE_STRIP_QUOTE, '', text)
    
    strongpronoun = re.search(RE_STRONGPRONOUN, stripped)
    weakpronoun = re.search(RE_WEAKPRONOUN, stripped)
    conjunctive = re.search(RE_CONJUNCTIVE, stripped)
    addons = re.search(RE_ADDONS, stripped)
    question = re.search(RE_QUESTION, stripped)

    interimhubelcount = 0.0
    if conjunctive: interimhubelcount += 0.4
    if strongpronoun: interimhubelcount += 0.4
    elif weakpronoun: interimhubelcount += 0.2
    if addons: interimhubelcount += 0.1
    if question: interimhubelcount -= 0.2

    if interimhubelcount > 1.0: interimhubelcount = 1.0
    if strongpronoun and conjunctive and addons: interimhubelcount = 42.23

    return interimhubelcount

## hubelmeter-precondition

def prehubelmeter(bot, event):
    if event.userhost in bot.ignore: return False
    if len(event.txt) > 0 and event.txt[0] == '!': return False

    interimhubelcount = checkhubel(event.txt)
    print interimhubelcount

    user = getuser(event).lower()
    i = HubelItem(user)
    # increase linecounter only
    i.data.rowcount += 1.0

    if interimhubelcount >= 0.6:
        if state:
            if not state['hubel']:
                state['hubel'] = []
        state['hubel'].append(event.txt)
        state.save()

        if interimhubelcount == 42.23:
            interimhubelcount = 1.0
            i.data.hubelcount += interimhubelcount
            if event.channel != '#c-base':
                event.reply('C-C-C-Combobreaker: %s hat %f hubel' % (user, i.hubel()))
        else:
            i.data.hubelcount += interimhubelcount
            if event.channel != '#c-base':
                event.reply('%s: %s (%s hat %f hubel)' % (user, random.choice(warntxt), user, i.hubel()))
        i.save()
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
    event.reply("hubelmeter for %s has been desubjunctivised." % item)

cmnds.add('hubelmeter-reset', handle_hubelmeter_reset, ['OPER'])

warntxt=[
    "Hubeln entfernt Ihre Gesundheit.",
    "Hubler sterben früher.",
    "Hubeln kann tödlich sein.",
    "Hubeln lässt ihre Haut altern.",
    "Hubeln kann die Spermatozoen schädigen und schränkt die Fruchtbarkeit ein.",
    "Hier finden Sie Hilfe, wenn Sie das Hubeln aufgeben möchten: Bundeszentrale für Enthubelung (BZE) https://community.c-base.org/group/c-prime",
    "Ihr Arzt oder Apotheker (Dr. Housetier) kann Ihnen dabei helfen, das Hubeln aufzugeben.",
    "Hubeln in der Schwangerschaft schadet Ihrem Kind.",
    "Schützen Sie Kinder – lassen Sie sie nicht Ihr Rumgehubel hören!",
    "Hubeln macht sehr schnell abhängig: Fangen Sie gar nicht erst an!",
    "Wer das Hubeln aufgibt, verringert das Risiko tödlicher Prokrastination.",
    "Hubeln kann zu einem langsamen und schmerzhaften Tod führen.",
    "Hubeln kann die Spermatozoen schädigen und schränkt die Fruchtbarkeit ein.",
    "Hubeln fügt ihnen und den Nerds in ihrer Umgebung erheblichen Schaden zu."
    ]

def handle_hubelwarn(bot, ievent):
    ievent.reply(random.choice(warntxt))

cmnds.add('hubelwarn', handle_hubelwarn, ['OPER', 'USER', 'GUEST'])

def handle_hubelsubmit(bot, ievent):
    hubel = HubelList("Hubel")
    nr = hubel.add(ievent.rest)
    ievent.reply("Der Hubel wurde als Nr. %d hinzugefügt. Vielen Dank." % nr)

cmnds.add('hubel-submit', handle_hubelsubmit, ['OPER', 'USER', 'GUEST'])

def handle_hubeldelete(bot, ievent):
    hubel = HubelList("Hubel")
    nr = int(ievent.rest)
    hubel.delete(nr)
    ievent.reply("Hubel Nr. %d wurde entfernt." % nr)

cmnds.add('hubel-delete', handle_hubeldelete, ['OPER', 'HUBELOPER'])

#TODO ijon cmnds.add('hubel-learn', handle_add, ['OPER', 'USER', 'GUEST'])

def handle_hubelreview(bot, ievent):
    hubel = HubelList("Hubel")
    sayhubel(bot, ievent, hubel['list'])
    #ievent.reply()

cmnds.add('hubel-review', handle_hubelreview, ['OPER', 'USER', 'GUEST'])

def handle_hubelclear(bot, ievent):
    hubel = HubelList("Hubel")
    hubel.clear()
    ievent.reply("Alle Hubel wurden entfernt.")

cmnds.add('hubel-clear', handle_hubelclear, ['OPER', 'HUBELOPER'])

def handle_hubelcheck(bot, ievent):
    ievent.reply("Der interimshubel beträgt %f" % checkhubel(ievent.txt))

cmnds.add('hubel-check', handle_hubelcheck, ['USER', 'GUEST', 'OPER', 'HUBELOPER'])

def handle_hubeldispute(bot, ievent):
    hubel = HubelList("Hubel")
    nr = hubel.add("DISPUTED: %s" % ievent.rest)
    ievent.reply("Der Dispute wurde als Nr. %d zum Review angenommen. Vielen Dank." % nr)

cmnds.add('hubel-dispute', handle_hubeldispute, ['OPER', 'USER', 'GUEST'])

def handle_hubeldiscard(bot, ievent):
    user = ievent.rest.split(' ')[0]
    i = HubelItem(user)
    interimhubel = checkhubel(ievent.rest)
    if interimhubel == 42.23: interimhubel = 1.0
    i.data.hubelcount = i.data.hubelcount - interimhubel
    i.save()
    ievent.reply("Der Hubel von %s wurde ordnungsgema:C verringert. (%f)" % (user, i.data.hubelcount/i.data.rowcount))
    
cmnds.add('hubel-discard', handle_hubeldiscard, ['OPER'])
    

def sayhubel(bot, ievent, hubellist):
    """ output hubel items. """
    if not hubellist: ievent.reply('Keine Hubel zum Review vorhanden.') ; return
    result = []
    counter = 1
    for i in hubellist:
        res = ""
        res += "%s) " % counter
        counter += 1
        res += "%s " % i.txt
        result.append(res.strip())
    if result: ievent.reply("Hubel zum Review: %s" % " ".join(result))

