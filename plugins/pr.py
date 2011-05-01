# jsb.plugs.common/pr.py
#
#

## jsb imports

from jsb.lib.callbacks import callbacks
from jsb.lib.commands import cmnds
from jsb.lib.examples import examples
from jsb.lib.persist import PlugPersist
from jsb.utils.statdict import StatDict
from jsb.lib.datadir import getdatadir
from jsb.utils.thomas import Bayes

## basic imports

import logging
import re
import os

## defines

## PRItem class

class PRItem(PlugPersist):

     def __init__(self, name, default={}):
         PlugPersist.__init__(self, name)
         self.data.name = name
         self.data.count = self.data.count or 0


class PR():

    def __init__(self):
        brainfile = open(os.path.join(getdatadir() + os.sep + 'plugs' + os.sep + 'myplugs.common.pr', 'brain'), 'r')

        self.guesser = {}
        currentguesser=''

        print "" #just a new line
        for line in brainfile.readlines():
            if (line.startswith('!')):
                currentguesser=line.strip()[1:]
                self.guesser[currentguesser] = Bayes()

            if line.__contains__(":"):
                s=line.strip().split(':')
                self.guesser[currentguesser].train(s[0].strip().lower(),s[1].strip().lower())
        brainfile.close()

    def guessCmd(self, s):
        return self.guesser['cmd'].guess(s.lower())

    def guessTimeParam(self, s):
        return self.guesser['time'].guess(s.lower())

    def getTimeString(self, line):
        guess = self.guesser['time'].guess(line.lower())
        print guess
        if guess.__len__() == 1:
            return guess[0][0]
        else:
            val = 0
            for o in guess:
                if o[1] > 0.5:
                    if o[0] == "+15":
                        val = val+15
                    elif o[0] == "-15":
                        val = val-55
                    elif o[0] == "-30":
                        val = val-70
                    else:
                        val = val + int (o[0])

        return str(val)

    def getCommandString(self, line):
        line = line.strip().lower()
        print line
        s = ""
        cmd = self.guesser['cmd'].guess(line)
        print 'cmd: %s' % cmd
        if cmd[0][1] < 0.5:
            return "too fuzzy"

        s=cmd[0][0]
        print s
        if (s == "eta"):
            time = self.getTimeString(line)
            s = s + " " + time
        return s

cpr = PR()

## pr precondition

def prepr(bot, event):
    #return False
    if event.userhost in bot.ignore: return False
    # do the pr

    if event.txt.lower().find(bot.cfg.nick.lower()) == -1:
        return False

    if len(event.txt) > 0 and event.txt[0] != '!':
        ret = '!%s' % cpr.getCommandString(event.txt)
        print "testing: %s | returned: %s" % (event.txt, ret)
        event.txt = ret
        if ret == '!volup':
            event.txt = '!mpd-volume up'
        elif ret == '!voldown':
            event.txt = '!mpd-volume down'
        elif ret == '!eta0':
            event.txt = '!eta 0'
        bot.putevent(event.userhost, event.channel, event.txt, event)
        #if event.txt == 'wer ist da?':
        #    event.txt = '!ul'
        #    bot.putevent(event)
        print 'DONE'
        return True
    return False

## pr callbacks

def prcb(bot, event):
    event.bind(bot)

    return 0

callbacks.add('PRIVMSG', prcb, prepr)
callbacks.add('MESSAGE', prcb, prepr)
callbacks.add('CONSOLE', prcb, prepr)

## pr command

def handle_pr(bot, event):
    if not event.rest: event.missing("<what>") ; return
    k = event.rest.lower()
    item = PRItem(event.channel.lower() + "-" + k)
    if item.data.count: event.reply("pr of %s is %s" % (k, item.data.count))
    else: event.reply("%s doesn't have pr yet." % k)

cmnds.add('pr', handle_pr, ['USER', ])
examples.add('pr', 'show pr', 'pr jsb')
