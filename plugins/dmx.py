# jsb.plugs.common/dmx.py
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
import jsonrpclib

cfg = PersistConfig()
cfg.define('rpcurl', 'http://localhost:8080')


jsonrpclib.config.version = 1.0
server = jsonrpclib.Server(cfg.get('rpcurl'))

#class DMXItem(PlugPersist):
#     def __init__(self, name, default={}):
#         PlugPersist.__init__(self, name)
#         self.data.name = name
#         self.data.orders = self.data.orders or {}

#dmxitem = DMXItem('dmx')

class DMXError(Exception): pass

def init():
    return 1

def shutdown():
    return 1

## dmx command

def handle_dmx(bot, ievent):
    ievent.reply('not implemented yet')

def handle_dmx_program(bot, ievent):
    program = 0
    try:    program = int(ievent.args[0])
    except: pass
    try:
        server.setprogram(program)
        ievent.reply('aye, program %s has been set' % program)
    except DMXError, e:
        ievent.reply(str(s))

def handle_dmx_color(bot, ievent):
    color = 'white'
    try:    color = ievent.args[0]
    except: pass
    
    try:
        if server.setcolor(color) == 0:
            ievent.reply('aye, color %s has been set' % color)
        else:
            ievent.reply('I don\'t know the color %s' % color)
            
    except DMXError, e:
        ievent.reply(str(s))

def handle_dmx_on(bot, ievent):
    try:
        if server.on() == 0:
            ievent.reply('aye')
        else:
            ievent.reply('I don\'t know how to turn it on - help!')
            
    except DMXError, e:
        ievent.reply(str(s))

def handle_dmx_off(bot, ievent):
    try:
        if server.off() == 0:
            ievent.reply('aye')
        else:
            ievent.reply('I don\'t know how to turn it off - help!')
            
    except DMXError, e:
        ievent.reply(str(s))

cmnds.add('dmx', handle_dmx_color, ['OPER'])
cmnds.add('dmx-color', handle_dmx_color, ['OPER'])
cmnds.add('dmx-program', handle_dmx_program, ['OPER'])
cmnds.add('dmx-on', handle_dmx_on, ['OPER'])
cmnds.add('dmx-off', handle_dmx_off, ['OPER'])
