# -*- coding: utf-8 -*-
"""
User handling views - get user info, nick spelling, wifi login settings.
"""

from django.utils import timezone

from ..json_rpc_client import jsonrpc_method
from .helpers import (
    getuser, getuser_eta, is_logged_in, models, userlist, userlist_with_online_percentage
)


@jsonrpc_method('get_user_by_id')
def get_user_by_id(request, id):
    """
    get information about a user using his id
    """
    u = models.User.objects.get(id=id)
    return u.dic()


@jsonrpc_method('get_user_by_name')
def get_user_by_name(request, username):
    """
    get information about a user using his nickname
    """
    u = models.User.objects.get(username=username)
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


@jsonrpc_method('autologout')
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
    now = int(timezone.now().strftime("%Y%m%d%H%M%S"))
    cl = {}
    for user in models.User.objects.filter(status="online"):
        td = timezone.now() - user.logintime
        cl[str(user)] = td.seconds
    return cl


def who_result():
    from .eta import etalist
    from .preferences import reminder
    return {
        'available': userlist(),
        'eta': etalist(),
        'etd': [],
        'lastlocation': {},
        'ceitloch': ceitloch(),
        'reminder': reminder()
    }


def userlist():
    return [str(user) for user in models.User.objects.filter(status="online").order_by('username')]


def userlist_with_online_percentage():
    return [str(user) + " (" + user.online_percentage() + "%)" for user in models.User.objects.filter(status="online").order_by('username')]


def is_logged_in(user):
    u = models.User.objects.filter(username=user)
    if len(u) > 0:
        u = u[0]
        if u.status == "online":
            return True
    return False
