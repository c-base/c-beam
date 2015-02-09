# -*- coding: utf-8 -*-

from jsb.lib.commands import cmnds

import random


def handle_dice(bot, ievent):
		ievent.reply(random.choice(['yes', 'no', 'elephant'))


cmnds.add("dice", handle_dice, ['OPER', 'USER', 'GUEST'])
