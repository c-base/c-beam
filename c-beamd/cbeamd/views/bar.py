"""
Bar status and prices.

Split out of the original views.py; function bodies are unchanged.
"""

import json

from django.http import HttpResponse
from django.shortcuts import render
from django.utils import timezone
from ..json_rpc_client import jsonrpc_method

from ..models import Status

from .helpers import c_leuse_c_out, logger
from .helpers import get_prices, publish, userlist


@jsonrpc_method('barschnur')
def barschnur(request, pizza, sushi, inder):
    publish("bar/schnur", "%d, %d, %d" % (pizza, sushi, inder))

    if pizza == 0 and sushi == 1 and inder == 1:
        # publish("c_out/play", "pizza")
        publish("c_out/announce", "eine pizza-bestellung wartet an der bar")
    if pizza == 1 and sushi == 0 and inder == 1:
        # publish("c_out/play", "sushi")
        publish("c_out/announce", "eine sushi-bestellung wartet an der bar")
    if pizza == 1 and sushi == 1 and inder == 0:
        # publish("c_out/play", "inder")
        publish("c_out/announce", "eine inder-bestellung wartet an der bar")


@jsonrpc_method("trafotron")
def trafotron(request, value):
    newval = (value * 100) / 170
    # print("trafotron: " + str(newval))
    # logger.error("trafotron: " + str(newval))
    # os.system("amixer -c 0 set Master %d%%" % newval)
    try:
        logger.debug(c_leuse_c_out.setvolume(newval))
    except Exception as e:
        logger.error(e)


@jsonrpc_method("barstatus")
def barstatus(request, status):
    """
    set the bar status to status
    status can be "open" or "closed"
    """
    status_object = Status.objects.get()
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
    return Status.objects.get().bar_open


def notify_bar_opening():
    publish("bar/status", timezone.localtime(timezone.now()).strftime("%H:%M") + " bar opening")


def notify_bar_closing():
    publish("bar/status", timezone.localtime(timezone.now()).strftime("%H:%M") + " bar closing")


def bar_preise(request):
    return render(request, 'cbeamd/bar_preise.django', {'prices': get_prices()})


def bar_leergut(request):
    return render(request, 'cbeamd/bar_leergut.django', {})


def bar_calc(request):
    return render(request, 'cbeamd/bar_calc.django', {'prices': get_prices()})


def bar_abrechnung(request):
    return render(request, 'cbeamd/bar_abrechnung.django', {})


def mechblast_json(request):
    return HttpResponse(json.dumps({'userlist': userlist(), 'barstatus': get_barstatus(request)}), content_type="application/json")
