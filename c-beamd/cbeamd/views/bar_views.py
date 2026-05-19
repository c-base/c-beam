# -*- coding: utf-8 -*-
"""
Bar operations views - bar status, prices, orders.
"""

import json
from datetime import timedelta

from django.http import HttpResponse
from django.shortcuts import render
from django.utils import timezone

from .. import models
from ..json_rpc_client import jsonrpc_method
from .view_helpers import c_out_volume, getuser, log_stats, publish, send_mail


@jsonrpc_method('barschnur')
def barschnur(request, pizza, sushi, inder):
    publish("bar/schnur", "%d, %d, %d" % (pizza, sushi, inder))

    if pizza == 0 and sushi == 1 and inder == 1:
        publish("c_out/announce", "eine pizza-bestellung wartet an der bar")
    if pizza == 1 and sushi == 0 and inder == 1:
        publish("c_out/announce", "eine sushi-bestellung wartet an der bar")
    if pizza == 1 and sushi == 1 and inder == 0:
        publish("c_out/announce", "eine inder-bestellung wartet an der bar")


@jsonrpc_method('c_portal.notify')
def c_portal_notify(request, notification):
    print(notification)


@jsonrpc_method("trafotron")
def trafotron(request, value):
    newval = (value * 100) / 170
    try:
        from .view_helpers import logger
        logger.debug(c_leuse_c_out.setvolume(newval))
    except Exception as e:
        logger.error(e)


@jsonrpc_method("barstatus")
def barstatus(request, status):
    """
    set the bar status to status
    status can be "open" or "closed"
    """
    status_object = models.Status.objects.get()
    if status == "open":
        status_object.bar_open = True
        status_object.save()
        notify_bar_opening()
    if status == "closed":
        status_object.bar_open = False
        status_object.save()
        notify_bar_closing()
    publish("bar/state", str(status), retain=True)


@jsonrpc_method("get_barstatus")
def get_barstatus(request):
    """
    get the current bar status
    """
    return models.Status.objects.get().bar_open


def notify_bar_opening():
    publish("bar/status", timezone.localtime(timezone.now()).strftime("%H:%M") + " bar opening")


def notify_bar_closing():
    publish("bar/status", timezone.localtime(timezone.now()).strftime("%H:%M") + " bar closing")


def bar_preise(request):
    from .view_helpers import get_prices
    return render(request, 'cbeamd/bar_preise.django', {'prices': get_prices()})


def bar_leergut(request):
    return render(request, 'cbeamd/bar_leergut.django', {})


def bar_calc(request):
    from .view_helpers import get_prices
    return render(request, 'cbeamd/bar_calc.django', {'prices': get_prices()})


def bar_abrechnung(request):
    return render(request, 'cbeamd/bar_abrechnung.django', {})


def get_prices():
    from .view_helpers import get_prices as _get_prices
    return _get_prices()


def mechblast_json(request):
    from .user_views import userlist
    return HttpResponse(json.dumps({'userlist': userlist(), 'barstatus': get_barstatus(request)}), content_type="application/json")
