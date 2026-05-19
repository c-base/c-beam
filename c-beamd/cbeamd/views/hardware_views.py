# -*- coding: utf-8 -*-
"""
Hardware storage and artefact views.
"""

import json
from django.http import HttpResponse
from django.shortcuts import render
from django.utils import timezone

from ..json_rpc_client import jsonrpc_method
from .view_helpers import (
    artefact_base_url, artefactcache, artefactcache_time, hwstorage_state, models, publish
)


def smile(request):
    return render(request, 'cbeamd/smile.django', {})


def bluewall(request):
    return render(request, 'cbeamd/bluewall.django', {})


def darkwall(request):
    return render(request, 'cbeamd/darkwall.django', {})


@jsonrpc_method('hwstorage')
def hwstorage(request, state):
    global hwstorage_state
    hwstorage_state = state
    publish("hwstorage/state", state, retain=True)

    def close():
        global hwstorage_state
        hwstorage_state = "closed"
        publish("hwstorage/state", "closed", retain=True)

    if state == "open":
        from threading import Timer
        timer = Timer(60, close)
        timer.start()

    return "aye"


def hwstorage_web(request):
    return render(request, 'cbeamd/hwstorage.django', {'hwstorage_state': hwstorage_state})


@jsonrpc_method('artefact_list')
def artefact_list(request):
    """
    returns a list of artefacts
    """
    from datetime import timedelta
    from urllib.request import urlopen

    global artefactcache, artefactcache_time
    if artefactcache_time + timedelta(hours=1) > timezone.now():
        return artefactcache

    try:
        result = urlopen(artefact_base_url + "json").read()
        artefactcache = json.loads(result)
        artefactcache_time = timezone.now()
    except Exception:
        pass

    return artefactcache


def artefact_base_url_view(request):
    return artefact_base_url


def artefact_list_web(request):
    return render(request, 'cbeamd/artefact_list.django', {'artefacts': artefact_list(request)})


def list_articles(request):
    from urllib.request import urlopen
    import feedparser

    try:
        d = feedparser.parse('https://www.c-base.org/blog/feed/')
    except Exception:
        d = None

    articles = []
    if d is not None:
        for entry in d['entries'][:10]:
            articles.append({
                'title': entry['title'],
                'link': entry['link'],
                'summary': entry.get('summary', ''),
                'published': entry.get('published', ''),
            })
    return articles


@jsonrpc_method('log_stats')
def log_stats_view():
    from .view_helpers import log_stats
    log_stats()
    return "aye"


@jsonrpc_method('get_stats')
def get_stats_view():
    from .view_helpers import get_stats
    return get_stats()


def list_portal_articles(request):
    return list_articles(request)


def app_data(request):
    from .event_views import event_list
    from .eta_views import etalist
    from .user_views import userlist
    return {
        'events': event_list(request),
        'eta': etalist(),
        'users': userlist(),
    }
