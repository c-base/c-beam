# jsb/plugs/common/define.py
#
#

""" define information items .. facts .. factoids. """

## jsb imports

from jsb.lib.callbacks import callbacks
from jsb.lib.commands import cmnds
from jsb.lib.examples import examples
from jsb.utils.lazydict import LazyDict
from jsb.lib.persist import PlugPersist, GlobalPersist

## basic imports

import logging, re

## define command

def handle_define(bot, event):
    """" arguments: <item> <description> - set an information item. """
    if not event.rest: 
        event.missing("<item> <description>") ; return

    if event.rest.startswith('"'):
        result = re.match(r'"(.*?)" (.*)$', event.rest)
    else:
        result = re.match(r'(.*?) (.*)$', event.rest)
    if result == None:
        return handle_whatis(bot, event)
    else:
        what = result.group(1)
        description = result.group(2)
    what = what.lower()
    items = GlobalPersist("definedb")
    if not items.data: items.data = LazyDict()
    if not items.data.has_key(what): items.data[what] = []
    if description not in items.data[what]: items.data[what].append(description)
    items.save()
    if event.channel == "#c-base":
        bot.say(event.channel, "definition for %s updated" % what)
    else:
        event.reply("definition for %s updated" % what)

cmnds.add('define', handle_define, ['OPER', 'USER', 'GUEST'])
examples.add('define', 'define the bot a description of an item.', "define dunk is botpapa")

## define-chan command

def handle_definechan(bot, event):
    """" arguments: <item> <description> - set an information item. """
    if not event.rest: event.missing("<item> <description>") ; return
    
    if event.rest.startswith('"'):
        result = re.search(r'"(.*?)" (.*)$', event.rest)
    else:
        result = re.search(r'(.*?) (.*)$', event.rest)
    try:
        what = result.group(0)
        description = result.group(1)
    except ValueError: event.missing("<item> <description>") ; return
    what = what.lower()
    items = PlugPersist(event.channel)
    if not items.data: items.data = LazyDict()
    if not items.data.has_key(what): items.data[what] = []
    if description not in items.data[what]: items.data[what] = [description]
    items.save()
    event.reply("definition for %s updated" % (what, event.channel))

cmnds.add('define-chan', handle_definechan, ['OPER', 'USER', 'GUEST'])
examples.add('define-chan', 'define the bot a description of an item. (channel specific)', "define-chan dunk is botpapa")

## forget command

def handle_forget(bot, event):
    """" arguments: <item> and <matchstring> - set an information item. """
    if not event.rest: event.missing("<item> and <match>") ; return
    try: (what, match) = event.rest.split(" and ", 2)
    except ValueError: what = event.rest ; match = None
    what = what.lower()
    items = GlobalPersist("definedb")
    got = False
    if not items.data: items.data = LazyDict()
    if items.data.has_key(what):
        if match == None: del items.data[what] ; got = True
        else:
            for i in range(len(items.data[what])):
                if match in items.data[what][i]:
                    del items.data[what][i]                
                    got = True
                    break
    if got: items.save() ; event.reply("item removed from global database")
    else: event.reply("no %s item in global database" % what)

cmnds.add('forget', handle_forget, ['OPER', 'USER'])
examples.add('forget', 'forget a description of an item.', "forget dunk and botpapa")

## forget-chan command

def handle_forgetchan(bot, event):
    """" arguments: <item> and <matchstring> - set an information item. """
    if not event.rest: event.missing("<item> and <match>") ; return
    try: (what, match) = event.rest.split(" and ", 2)
    except ValueError: what = event.rest ; match = None
    what = what.lower()
    items = PlugPersist(event.channel)
    got = False
    if not items.data: items.data = LazyDict()
    if items.data.has_key(what):
        if match == None: del items.data[what] ; got = True
        else:
            for i in range(len(items.data[what])):
                if match in items.data[what][i]:
                    del items.data[what][i]                
                    got = True
                    break
    if got: items.save() ; event.reply("item removed from %s database" % event.channel)
    else: event.reply("no %s item in channel database" % what)

cmnds.add('forget-chan', handle_forgetchan, ['OPER', 'USER'])
examples.add('forget-chan', 'forget a description of an item. (channel specific)', "forget-chan dunk and botpapa")

## whatis command

def handle_whatis(bot, event):
    """ arguments: <item> - show what the bot has defineed about a factoid. """
    if not event.rest: event.missing("<what>") ; return
    if event.rest.startswith('"'):
        result = re.search(r'"(.*?)"$', event.rest)
    else:
        result = re.search(r'(.*?)$', event.rest)
    what = result.group(1).lower()
    items = PlugPersist(event.channel)
    result = []
    if what in items.data and items.data[what]: result = [items.data[what][-1]]
    globalitems = GlobalPersist("definedb")
    if what in globalitems.data and globalitems.data[what]: result.append(globalitems.data[what][-1])

    if result: reply = "%s: %s" % (event.rest, ", ".join(result))
    else: reply = "sorry, no definition found for '%s'... wanna cre8 one? #define <word> <definition>" % what

    if event.channel == "#c-base":
        bot.say(event.channel, reply)
    else:
        event.reply(reply)

cmnds.add('whatis', handle_whatis, ['OPER', 'USER', 'GUEST'])
examples.add("whatis", "whatis defineed about a subject", "whatis jsb")

## items command

def handle_items(bot, event):
    """ no arguments - show what items the bot has defineed. """
    items = PlugPersist(event.channel).data.keys()
    globalitems = GlobalPersist("definedb").data.keys()
    result = items + globalitems
    event.reply("i know %s items: " % len(result), result)

cmnds.add('items', handle_items, ['OPER', 'USER', 'GUEST'])
examples.add("items", "show what items the bot knows", "items")

# searchitems command

def handle_searchitems(bot, event):
    """ argument: <searchtxt>  - search the items the bot has defineed. """
    if not event.rest: event.missing("<searchtxt>") ; return
    items = PlugPersist(event.channel).data.keys()
    globalitems = GlobalPersist("definedb").data.keys()
    got = []
    for i in items + globalitems:
        if event.rest in i: got.append(i)
    event.reply("found %s items: " % len(got), got)

cmnds.add('searchitems', handle_searchitems, ['OPER', 'USER', 'GUEST'])
examples.add("searchitems", "search the items the bot knows", "searchitems jsonbot")

## define-toglobal command

def handle_definetoglobal(bot, event):
    """ argument: <searchtxt>  - search the items the bot has defineed. """
    items = PlugPersist(event.channel)
    globalitems = GlobalPersist("definedb")
    for i in items.data.keys():
        if not globalitems.data.has_key(i): globalitems.data[i] = []
        globalitems.data[i].extend(items.data)
    globalitems.save()
    event.reply("%s items copy to the global database. " % len(items.data))

cmnds.add('define-toglobal', handle_definetoglobal, ['OPER', ])
examples.add("define-toglobal", "move channel specific define data to the global database.", "define-toglobal")

## callbacks

def predefine(bot, event):
    """ define precondition. """
    if event.iscommand: return False
    if len(event.txt) < 2: return False
    #if event.txt and (event.txt[0] == "?" or event.txt[-1] == "?") and not event.forwarded: return True
    if event.txt and (event.txt[0] == "?") and not event.forwarded: return True
    return False

def definecb(bot, event):
    """ define callback, is for catching ? queries. """
    event.bind(bot)
    result = []
    items = PlugPersist(event.channel)
    target = event.txt.lower()
    if target[0] == "?": target = target[1:]
    if target[-1] == "?": target = target[:-1]
    if target in items.data: result = items.data[target]
    globalitems = GlobalPersist("definedb")
    if target in globalitems.data:
        if not target in result: result.extend(globalitems.data[target])    
    if result: event.reply("%s is " % target, result, dot=", ")
    event.ready()

callbacks.add("PRIVMSG", definecb, predefine)
callbacks.add("MESSAGE", definecb, predefine)
callbacks.add("DISPATCH", definecb, predefine)
callbacks.add("CONSOLE", definecb, predefine)
callbacks.add("CMND", definecb, predefine)
callbacks.add("TORNADO", definecb, predefine)
