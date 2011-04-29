# jsb.plugs.common/koffie.py
#
# Made by WildRover and Junke1990

""" schenk wat koffie! """

## jsb imports

from jsb.lib.commands import cmnds
from jsb.lib.examples import examples

## basic imports

import os
import string
import random

## defines

mate = []

## init function

def init():
    global mate
    for i in  matetxt.split('\n'):
        if i:
            mate.append(i.strip())
    return 1

## functions

def do(bot, ievent, txt):
    if not bot.isgae: bot.action(ievent.channel, txt)
    else: bot.say(ievent.channel, txt)

## commands

def handle_mate(bot, ievent):
    """ get a mate """
    rand = random.randint(0,len(mate)-1)
    try:
        input = ievent.args[0]
        nick = '%s' % input
    except:
        if len('%s') >= 0: nick = ievent.nick
    do(bot, ievent, mate[rand] + " " + nick)

cmnds.add('mate', handle_mate, 'USER')

matetxt = """ reicht eine leckere club mate an
wirft eine mate in richtung
prostet mit einer mate zu
"""

