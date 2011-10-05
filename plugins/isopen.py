# jsb/plugs/common/c-lang.py
# -*- coding: utf-8 -*-

## jsb imports

from jsb.utils.exception import handle_exception
from jsb.lib.commands import cmnds
from jsb.lib.examples import examples

## basic imports

import re, urllib
import random

## defines

## isopen command

def handle_isopen(bot, ievent):
    mysock = urllib.urlopen("http://shackspace.de/sopen/text/de")
    ievent.reply(mysock.read())

cmnds.add('isopen', handle_isopen, ['OPER', 'USER', 'GUEST'])
cmnds.add('offen', handle_isopen, ['OPER', 'USER', 'GUEST'])

