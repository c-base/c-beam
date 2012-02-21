# -*- coding: utf-8 -*-

from jsb.utils.exception import handle_exception
from jsb.lib.commands import cmnds

import datetime


def pose_as_nonsmoker(bot, ievent):
    if ievent.nick in ('dazz', 'dazs', 'dazs1', 'dass'):
        firstday = datetime.datetime(1999, 1, 1, 0, 0, 0)
        now = datetime.datetime.now()
        diff = now - firstday
        days = diff.days
        bot.say('#c-base', "dazs raucht jetzt seit über %i Tagen." % days)
    elif ievent.nick in ('rasda'):
        firstday = datetime.datetime(1987, 6, 23, 0, 0, 0)
        now = datetime.datetime.now()
        diff = now - firstday
        days = diff.days
        bot.say('#c-base', "%s raucht jetzt seit %i Tagen." % (ievent.nick, days))
    elif ievent.nick in ('baccenfutter'):
        firstday = datetime.datetime(2011, 12, 6, 0, 0, 0)
        now = datetime.datetime.now()
        diff = now - firstday
        days = diff.days
        bot.say('#c-base', "baccenfutter ist jetzt seit %i Tagen Nichtraucher." % days)
    elif ievent.nick in ('tacco'):
        bot.say('#c-base', "deine mudder.")
    else:
        bot.say('#c-base', "ich hab keine ahnung wie lange du schon rauchst oder nicht rauchst, %s." % ievent.nick)

cmnds.add("smoke", pose_as_nonsmoker, ['OPER', 'USER', 'GUEST'])
