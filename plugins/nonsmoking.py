from jsb.utils.exception import handle_exception
from jsb.lib.commands import cmnds

import datetime

firstday = datetime.datetime(2011, 12, 6, 0, 0, 0)

def pose_as_nonsmoker(bot, ievent):
    now = datetime.datetime.now()
    diff = now - firstday
    days = diff.days
    bot.say('#c-base', "baccenfutter ist jetzt seit %i Tagen Nichtraucher." % days)

cmnds.add("smoke", pose_as_nonsmoker, ['OPER', 'USER', 'GUEST'])
