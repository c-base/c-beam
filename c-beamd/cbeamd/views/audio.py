"""
c_out audio: TTS, sounds and volume.

Split out of the original views.py; function bodies are unchanged.
"""


from django.contrib.auth.decorators import login_required
from django.shortcuts import render
from ..json_rpc_client import jsonrpc_method

from ..models import User

from .helpers import cout, getuser, monitord, publish


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
    # try:
    #     result = cout.tts(voice, text)
    # except:
    #     pass
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
    # try:
        # result = cout.play(file)
    # except:
        # pass
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
        result = sorted(cout.sounds())
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


@login_required
def c_out_web(request):
    return render(request, 'cbeamd/c_out.django', {'sound_list': sounds(request)})


@login_required
def c_out_play_web(request, sound):
    result = play(request, sound)
    return render(request, 'cbeamd/c_out.django', {'sound_list': sounds(request), 'result': "sound wurde abgespielt"})


#################################################################
# reminder methods
#################################################################

@jsonrpc_method('remind')
def remind(user, reminder):
    u = getuser(user)
    u.reminder = reminder
    return "aye"


def reminder():
    result = {}
    for u in User.objects.filter(status="eta"):
        result[u.username] = u.reminder
    return result
