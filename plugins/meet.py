# jsb.plugs.common/meeting.py
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
cfg.define('meeting-timeout', 72000)

userpath = '/home/smile/users'
usermap = eval(open('%s/usermap' % cfg.get('datadir')).read())

class MeetItem(PlugPersist):
     def __init__(self, name, default={}):
         PlugPersist.__init__(self, name)
         self.data.name = name
         self.data.meetings = self.data.meetings or {}
         self.data.meetingtimestamps = self.data.meetingtimestamps or {}
         self.data.meetingsubs = self.data.meetingsubs or []
         self.data.opensubs = self.data.opensubs or []

meetingitem = MeetItem('meeting')

class MeetError(Exception): pass

def init():
    return 1

def shutdown():
    return 1

## meeting command

def handle_meeting(bot, ievent):
    """list all user that have logged in on the mirror."""
    if ievent.rest:
        params = ievent.rest.split(' ')
        print params
    else:
        print "no rest"

cmnds.add('meeting', handle_meeting, ['USER'])

