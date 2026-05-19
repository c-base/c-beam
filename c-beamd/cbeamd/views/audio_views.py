# -*- coding: utf-8 -*-
"""
Audio and TTS (Text-to-Speech) views - c_out, play, voices.
"""

from django.shortcuts import render

from ..json_rpc_client import jsonrpc_method
from .view_helpers import publish, reply


@jsonrpc_method('monmessage')
def monmessage(request, message):
    """
    display message on the display in the airlock (c_leuse)
    """
    try:
        monitord.message(message)
    except Exception:
        pass
    return "yo"


@jsonrpc_method('tts')
def tts(request, voice, text):
    """
    perform text-to-speech over c_out with voice saying text
    """
    result = "aye"
    return result


@jsonrpc_method('r2d2')
def r2d2(request, text):
    """
    perform text-to-r2d2 over c_out with voice saying text
    """
    return cout.r2d2(text)


@jsonrpc_method('play')
def play(request, file):
    """
    play sound file via c_out
    """
    result = "aye"
    if file == '':
        publish("c_out/loop", "")
    else:
        publish("c_out/play", str(file))
    return result


@jsonrpc_method('setvolume')
def setvolume(request, volume):
    """
    set c_out volume to volume
    """
    return cout.setvolume(volume)


@jsonrpc_method('getvolume')
def getvolume(request, volume):
    """
    get the current c_out volume
    """
    return cout.getvolume(volume)


@jsonrpc_method('voices')
def voices(request):
    """
    get a list of available voices for text-to-speech
    """
    return cout.voices()


@jsonrpc_method('sounds')
def sounds(request):
    """
    returns a list of sounds available to play via c_out
    """
    result = []
    try:
        result = sorted(cout.sounds()['result'])
    except Exception:
        pass
    return result


@jsonrpc_method('c_out')
def c_out(request):
    """
    plays a random sound via c_out
    """
    return cout.c_out()


@jsonrpc_method('announce')
def announce(request, text):
    """
    perform a text-to-speech announcement via c_out
    """
    result = "aye"
    publish("c_out/announce", str(text))
    try:
        result = cout.announce(text)
    except Exception:
        pass
    return result


def c_out_web(request):
    return c_out(request)


def c_out_play_web(request, sound):
    return play(request, sound)


@jsonrpc_method('remind')
def remind(request, user, text):
    from .preferences_views import reminder
    r = reminder()
    r[user] = text
    return "aye"


@jsonrpc_method('reminder')
def reminder_view(request):
    from .preferences_views import reminder
    return reminder()
