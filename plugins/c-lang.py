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

c_lang_exceptions = {
    'cristall': 'kristall',
    'cristaL': 'kristall',
    'baccenfuTer': 'baccenfutter',
    'baCenfuTer': 'baccenfutter',
    'baCenfutter': 'baccenfutter',
    'coc_':     'kosch',
    'cosch':    'kosch',
}

## c-lang command

def handle_c_lang(bot, ievent):
    text = "herzlich willkommen auf der c-base. schön daß du an board gekommen bist."
    if ievent.rest:
        text = ievent.rest
    ievent.reply(c_lang(text, 2))

def handle_c_lang2(bot, ievent):
    text = "herzlich willkommen auf der c-base. schön daß du an board gekommen bist."
    if ievent.rest:
        text = ievent.rest
    ievent.reply(c_lang(text, 3))

def c_lang(text, level):
    if not level:
        level = 1
    if level > 0:
        text = text.lower()
        text = re.sub(r'sch', r'c_', text)
    if level > 0:
        text = re.sub(r'ck([a-zA-Z])', r'cc\1', text)
        text = re.sub(r'k', r'c', text)
        text = re.sub(r'tzt', r'tCt', text)
        text = re.sub(r'z', r'c', text)
        text = re.sub(r'ß', r'C', text)
        text = re.sub(r'\xdf', r'C', text)
        text = re.sub(r'ss', r'C', text)
        text = re.sub(r'(^| )sy[bcdfghjklmnpqrstvwxyz]', r'cy', text)

    if level > 1:
        text = re.sub(r'ä', r'a:', text)
        text = re.sub(r'\xe4', r'a:', text)
        text = re.sub(r'ö', r'o:', text)
        text = re.sub(r'\xf6', r'o:', text)
        text = re.sub(r'ü', r'u:', text)
        text = re.sub(r'\xfc', r'u:', text)

    if level > 2:
        text = re.sub(r'll', r'L', text)
        text = re.sub(r'mm', r'M', text)
        text = re.sub(r'nn', r'N', text)
        text = re.sub(r'tt', r'T', text)
        text = re.sub(r'rr', r'R', text)
        text = re.sub(r'pp', r'P', text)


    for key in c_lang_exceptions:
        text = text.replace(key, c_lang_exceptions[key])
    return text

cmnds.add('c-lang', handle_c_lang, ['OPER', 'USER', 'GUEST'])
cmnds.add('c-lang2', handle_c_lang2, ['OPER', 'USER', 'GUEST'])
