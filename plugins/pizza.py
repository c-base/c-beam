# jsb.plugs.common/pizza.py
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

usermap = eval(open('%s/usermap' % cfg.get('datadir')).read())

class PizzaItem(PlugPersist):
     def __init__(self, name, default={}):
         PlugPersist.__init__(self, name)
         self.data.name = name
         self.data.orders = self.data.orders or {}
         self.data.orderer = self.data.orderer or ''
         self.data.dealer = self.data.dealer or ''

pizzaitem = PizzaItem('pizza')

class PizzaError(Exception): pass

def init():
    return 1

def shutdown():
    return 1

def pizza():
    return os.listdir(userpath)

## pizza command

def handle_pizza(bot, ievent):
    """pizza ordering."""
    if not ievent.args:        
        return handle_pizza_list(bot, ievent)
    else:
        if not pizzaitem.data.orderer:
            ievent.reply('No one is ordering pizza at the moment. To start a new order type !pizza-start <pizza dealer>.')
        else:
            # check order
            print ievent.args[-1]
            ievent.args[-1].replace(',','.')
            try: price = float(ievent.args[-1].replace(',','.'))
            except: ievent.reply('Use !pizza <your pizza> <price>'); return
            
            # add order to the list
            user = getuser(ievent)
            if not user:
                ievent.reply('I do not know your nickname, sorry')
                return
            order = [' '.join(ievent.args[0:-1]), price]
            if user in pizzaitem.data.orders.keys():
                pizzaitem.data.orders[user].append(order)
            else:
                pizzaitem.data.orders[user] = [order]
            pizzaitem.save()
            return handle_pizza_list(bot, ievent)

def getuser(ievent):
    if ievent.channel in usermap:
        return usermap[ievent.channel]
    elif ievent.fromm in usermap:
        return usermap[ievent.fromm]
    elif ievent.channel.find('c-base.org') > -1:
        print ievent.channel[:-10]
        return ievent.channel[:-10]
    elif ievent.fromm.find('c-base.org') > -1:
        print ievent.fromm[:-10]
        return ievent.fromm[:-10]
    else:
        return 0

def handle_pizza_list(bot, ievent):
    user = getuser(ievent)
    reply = ''
    if not user:
        ievent.reply('I do not know your nickname, sorry')
        return
    if user == pizzaitem.data.orderer:
        for user in pizzaitem.data.orders.keys():
            total = 0.0
            i = 1
            for pizza in pizzaitem.data.orders[user]:
                reply += '%s: #%d %s %.2f\n' % (i, user, pizza[0], pizza[1])
                total += pizza[1]
                i += 1
            reply += '%s total: %.2f\n' % (user, total)
        ievent.reply(reply)
    else:
        if user in pizzaitem.data.orders.keys():
            total = 0.0
            for pizza in pizzaitem.data.orders[user]:
                reply += '%s: %s %.2f\n' % (user, pizza[0], pizza[1])
                total += pizza[1]
            reply += '%s total: %.2f\n' % (user, total)
            ievent.reply(str(reply))
        else:
            ievent.reply('I don\'t think you\'ve ordered anything yet.')

def handle_pizza_start(bot, ievent):
    if not ievent.args:
        ievent.missing('<pizza dealer>') ; return
    dealer = " ".join(ievent.args)
    if not pizzaitem.data.orderer:
        user = getuser(ievent)
        if not user:
            ievent.reply('I do not know your nickname, sorry')
            return
        pizzaitem.data.orderer = user
        pizzaitem.data.dealer = dealer
        pizzaitem.save()
        ievent.reply('%s: You are now the orderer of the next order. Thank you :)' % pizzaitem.data.orderer)
    else:
        ievent.reply('%s is already ordering pizza, you can order a pizza with !pizza <your pizza> <price>' % pizzaitem.data.orderer)

def handle_pizza_cancel(bot, ievent):
    pizzaitem.data.orderer = ''
    pizzaitem.data.dealer = ''
    pizzaitem.data.orders = {}
    pizzaitem.save()
    ievent.reply('Order canceled.')

cmnds.add('pizza', handle_pizza, ['USER'])
cmnds.add('pizza-list', handle_pizza_list, ['USER'])
cmnds.add('pizza-start', handle_pizza_start, ['USER'])
cmnds.add('pizza-cancel', handle_pizza_cancel, ['OPER'])
