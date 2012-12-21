# -*- coding: utf-8 -*-

from jsb.utils.exception import handle_exception
from jsb.lib.commands import cmnds

import datetime, random

fridaymessages = ["Hail Eris it's Friday!", "Heute \o/", "wochenende++", "Wir haben Freitag.", "HEIF!", "c-beam verschwindet ins wochenende", "endlich wochenende.", "freitag - heute - wohooo!"]

def handle_friday(bot, ievent):
        weekday = datetime.datetime.now().weekday()
        friday = 4
        days = friday-weekday
        if weekday < 4:
            if days == 1:
                message = "Nur noch ein Tag, dann ist Freitag \o/"
            else:
                message = "Noch %d Tage bis Freitag" % days
        elif weekday == 4:
            message = random.choice(fridaymessages)
        else:
            days += 7
            message = "Noch %d Tage bis Freitag" % days
        bot.say('#c-base', message)
        #ievent.reply(message)


cmnds.add("friday", handle_friday, ['OPER', 'USER', 'GUEST'])
