"""
Hardware and artefacts

Split out of the original views.py; function bodies are unchanged.
"""

import sys
import traceback
from threading import Timer
from urllib.request import urlopen

from django.shortcuts import render
from django.utils import timezone
from ..json_rpc_client import jsonrpc_method

from ..models import Mission
from ..tools.LEDStripe import *
from ..tools.MyHTMLParser import MyHTMLParser

from . import helpers
from .helpers import logger
from .activity import activitylog
from .audio import sounds
from .bar import get_barstatus
from .events import event_list
from .web import stats_list, user_list


@jsonrpc_method('smile', authenticated=True)
def smile(request):
    return "aye"


@jsonrpc_method('bluewall()')  # , authenticated=True, validate=True)
def bluewall(request):
    return "culd not available"


@jsonrpc_method('darkwall()')  # , authenticated=True, validate=True)
def darkwall(request):
    return "culd not available"


# @jsonrpc_method('hwstorage(Boolean)', authenticated=True, validate=True)
@jsonrpc_method('hwstorage')
def hwstorage(request):
    global timer
    # global hwstorage_state
    # if hwstorage_state == "open":
    # return
    # hwstorage_state = "open"

    def close():
        # hwstorage_state = "closed"
        pass
    timer = Timer(30.0, close)
    timer.start()
    return "aye"


def hwstorage_web(request):
    result = hwstorage(request, True)
    return render(request, 'cbeamd/c_buttons.django', {'result': 'Software-Endlager wurde geöffnet: %s' % result})


@jsonrpc_method('artefact_list')
def artefact_list(request):
    """
    returns a list of available artefacts
    """
    global artefact_base_url
    artefactlist = {}
    if True:  # artefactcache_time + timedelta(hours=1) < timezone.now():
        parser = MyHTMLParser()
        try:
            response = urlopen("http://10.0.1.44/artefact/").read().decode('utf-8')
            parser.feed(response)
            artefacts = parser.get_artefacts()
            artefactlist = [{'name': key, 'slug': artefacts[key]} for key in artefacts.keys()]
            helpers.artefactcache = artefactlist
            helpers.artefactcache_time = timezone.now()
        except Exception as e:
            logger.error(e)
            traceback.print_exc(file=sys.stdout)
    else:
        artefactlist = helpers.artefactcache
    # return sorted(artefactlist)
    return artefactlist


@jsonrpc_method('artefact_base_url')
def artefact_base_url(request):
    """
    returns the base URL for artefacts
    """
    global artefact_base_url
    return [artefact_base_url]


def artefact_list_web(request):
    return render(request, 'cbeamd/artefact_list.django', {'artefact_list': artefact_list(request)})


@jsonrpc_method('app_data')
def app_data(request):
    """
    returns a large data structure that contains all current status information that is required by the c-beam app
    """
    missions = [mission.dic() for mission in Mission.objects.order_by('-status', 'short_description')]
    return {'user': user_list(request), 'events': event_list(request), 'artefacts': artefact_list(request), 'missions': missions, 'activitylog': activitylog(request), 'stats': stats_list(request), 'barstatus': get_barstatus(request), 'sounds': sounds(request)}
