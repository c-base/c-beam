# jsb/plugs/common/circle.py
#
#

""" run the eight ball. """

## jsb imports

from jsb.utils.exception import handle_exception
from jsb.lib.commands import cmnds
from jsb.lib.examples import examples
import datetime

## basic imports

## defines

## circle command

def handle_circle(bot, ievent):
    """ tell when the next circle should take place """
    circledate = datetime.datetime.now()
    circledate = circledate.replace(hour=20,minute=0, second=0)
    if circledate.day > 1 and circledate.day < 14:
        circledate = circledate.replace(day=14)
    else:
        circledate = circledate.replace(day=1)
        month = circledate.month + 1
        circledate = circledate.replace(month=month)

    ievent.reply("der na:chste circle wird am %s um 2000 stattgefunden haben." % circledate.strftime("%Y-%m-%d"))

cmnds.add('circle', handle_circle, ['OPER', 'USER', 'GUEST'])
