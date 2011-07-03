# jsb/plugs/common/c-lang.py
# -*- coding: utf-8 -*-

""" run the eight ball. """

## jsb imports

from jsb.utils.exception import handle_exception
from jsb.lib.commands import cmnds
from jsb.lib.examples import examples

## basic imports

import re
import random

## defines

## c-lang command

def handle_c_lang(bot, ievent):

    text = "herzlich willkommen auf der c-base. schön daß du an board gekommen bist."
    if ievent.rest:
        text = ievent.rest

    text = text.lower()

    text = re.sub(r'ck([a-zA-Z])', r'cc\1', text)
    text = re.sub(r'sch', r'c_', text)
    text = re.sub(r'ä', r'a:', text)
    text = re.sub(r'\xe4', r'a:', text)
    text = re.sub(r'ö', r'o:', text)
    text = re.sub(r'\xf6', r'o:', text)
    text = re.sub(r'ü', r'u:', text)
    text = re.sub(r'\xfc', r'u:', text)
    text = re.sub(r'ß', r'C', text)
    text = re.sub(r'\xdf', r'C', text)
    text = re.sub(r'ss', r'C', text)
    text = re.sub(r'k', r'c', text)
    text = re.sub(r'tzt', r'tCt', text)
    text = re.sub(r'z', r'c', text)
    text = re.sub(r'(^| )sy[bcdfghjklmnpqrstvwxyz]', r'cy', text)
    
    ievent.reply(text)

cmnds.add('c-lang', handle_c_lang, ['OPER', 'USER', 'GUEST'])
