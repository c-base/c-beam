# -*- coding: utf-8 -*-

from jsb.utils.exception import handle_exception
from jsb.lib.commands import cmnds

import os


def handle_ddate(bot, ievent):
        message = os.system('ddate')
        #bot.say('#c-base', message)
        ievent.reply(message)


cmnds.add("ddate", handle_ddate, ['OPER', 'USER', 'GUEST'])
