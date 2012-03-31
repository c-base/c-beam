# -*- coding: utf-8 -*-
# jsb.plugs.common/council.py
#
# Made by WildRover and Junke1990

""" schenk wat koffie! """

## jsb imports

from jsb.lib.commands import cmnds
from jsb.lib.examples import examples
from jsb.lib.persist import PlugPersist
from jsb.utils.statdict import StatDict
from jsb.lib.persistconfig import PersistConfig
from jsb.lib.persiststate import UserState
from jsb.utils.lazydict import LazyDict
from jsb.lib.persiststate import PlugState

## basic imports

import councilclasses

## defines

class CouncilList(UserState):

    def __init__(self, name, *args, **kwargs):
        UserState.__init__(self, name, "council", *args, **kwargs)
        if self.data.list: self.data.list = [LazyDict(x) for x in self.data.list]
        else: self.data.list = []
        self.name = name

    def add(self, title, owner):
        """ add a council """
        council = Council(title, owner)
        self.data.list.append(council)
        self.save()
        return len(self.data.list)

    def delete(self, indexnr):
        """ delete a council. """
        del self.data.list[indexnr-1]
        self.save()
        return self

    def clear(self):
        """ clear the council list. """
        self.data.list = []
        self.save()
        return self

## init function

def init():
    global initdone
    state = PlugState()
    state.define('council', {})
    initdone = True
    return 1


## functions

## commands

def handle_council(bot, ievent):
    """ get a council """
    rand = random.randint(0,len(council)-1)
    try:
        input = ievent.args[0]
        nick = '%s' % input
    except:
        if len('%s') >= 0: nick = ievent.nick
    do(bot, ievent, council[rand] + " " + nick)

cmnds.add('council', handle_council, 'USER')

def handle_council_add(bot, ievent):
    councilList = CouncilList(ievent.channel)
    title = "foo"
    owner = "bar"
    nr = councilList.add(title, owner)
    ievent.reply("Der Council wurde als Nr. %d für den channel %s hinzugefügt. Vielen Dank." % (nr, ievent.channel))

cmnds.add('council-add', handle_council, 'USER')

def handle_council_o7(bot, ievent):
    ievent.reply(ievent.channel)
    councilList = CouncilList(ievent.channel)
    # check if council is open in the channel
    #if councilList.getRunning(ievent.channel)
    #return 
    # add the user to the running council

cmnds.add('o7', handle_council_o7, 'USER')

