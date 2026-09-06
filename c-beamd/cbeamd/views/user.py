"""
User information and per-user settings.

Split out of the original views.py; function bodies are unchanged.
"""


from django.utils import timezone
from ..json_rpc_client import jsonrpc_method

from ..models import User

from .audio import reminder
from .helpers import getuser, userlist


@jsonrpc_method('get_user_by_id')
def get_user_by_id(request, id):
    """
    get information about a user using his id
    """
    u = User.objects.get(id=id)
    return u.dic()


@jsonrpc_method('get_user_by_name')
def get_user_by_name(request, username):
    """
    get information about a user using his nickname
    """
    u = User.objects.get(username=username)
    return u.dic()


@jsonrpc_method('getnickspell')
def getnickspell(request, user):
    u = getuser(user)
    if u.nickspell == "":
        return user
    else:
        return u.nickspell


@jsonrpc_method('setnickspell')
def setnickspell(request, user, nickspell):
    u = getuser(user)
    u.nickspell = nickspell
    u.save()
    return "ok"


@jsonrpc_method('setwlanlogin')
def setwlanlogin(request, user, enabled):
    u = getuser(user)
    u.wlanlogin = enabled
    u.save()


@jsonrpc_method('getwlanlogin')
def getwlanlogin(request, user):
    u = getuser(user)
    return u.wlanlogin


@jsonrpc_method('get_autologout')
def get_autologout(request, user):
    u = getuser(user)
    return u.autologout


@jsonrpc_method('set_autologout')
def set_autologout(request, user, autologout):
    u = getuser(user)
    u.autologout = autologout
    u.save()
    return "aye"


def ceitloch():
    cl = {}
    for user in User.objects.filter(status="online"):
        td = timezone.now() - user.logintime
        cl[str(user)] = td.seconds
    return cl


def who_result():
    from .eta import etalist  # deferred: avoids user <-> eta import cycle
    return {
        'available': userlist(),
        'eta': etalist(),
        'etd': [],
        'lastlocation': {},
        'ceitloch': ceitloch(),
        'reminder': reminder()
    }
