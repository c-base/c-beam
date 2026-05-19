# -*- coding: utf-8 -*-
"""
Event handling views.
"""

import re
from urllib.request import urlopen

from django.shortcuts import render
from django.utils import timezone
from ics import Calendar

from ..json_rpc_client import jsonrpc_method
from .view_helpers import (
    eventcache, eventdetailcache, eventcache_time, publish
)


@jsonrpc_method('events')
def events(request):
    """
    get todays events
    """
    update_event_cache()
    return eventcache


@jsonrpc_method('event_list')
def event_list(request):
    """
    get todays events with details
    """
    update_event_cache()
    return eventdetailcache


@jsonrpc_method('event_detail')
def event_detail(request, id):
    """
    get details for event with id id
    """
    import feedparser
    d = feedparser.parse('http://www.c-base.org/calender/phpicalendar/rss/rss2.0.php?cal=&cpath=&rssview=today')
    for entry in d['entries']:
        title = re.search(r'.*: (.*)', entry['title']).group(1)
        end = re.search(r'(\d\d\d\d-\d\d-\d\d)T(\d\d:\d\d):(\d\d)', entry['ev_enddate']).group(2).replace(':', '')
        start = re.search(r'(\d\d\d\d-\d\d-\d\d)T(\d\d:\d\d):(\d\d)', entry['ev_startdate']).group(2).replace(':', '')
        title = title.replace("c   user", "c++ user")
    return "aye"


def update_event_cache():
    global eventcache_time, eventcache, eventdetailcache
    if eventcache_time.day == timezone.now().day:
        return

    events = []
    event_details = []

    url = 'https://www.c-base.org/calendar/exported/c-base-events.ics'
    c = Calendar(urlopen(url).read().decode('utf-8'))

    if c is not None:
        from datetime import date
        for entry in c.events:
            entryid = 42
            try:
                entryid = entry.uid
            except Exception:
                pass

            title = entry.name
            end = re.search(r'(\d\d\d\d-\d\d-\d\d)T(\d\d:\d\d):(\d\d)', str(entry.end)).group(2).replace(':', '')
            start = re.search(r'(\d\d\d\d-\d\d-\d\d)T(\d\d:\d\d):(\d\d)', str(entry.begin)).group(2).replace(':', '')

            if isinstance(title, str):
                title = title.replace("c   user", "c++ user")
            else:
                title = "-"
            if str(entry.begin).startswith(date.today().strftime("%Y-%m-%d")):
                description = entry.description
                events.append('%s (%s-%s)' % (title, start, end))
                event_details.append({'id': entryid, 'title': title, 'start': start, 'end': end, 'description': description})
        eventcache = events
        eventdetailcache = event_details
        eventcache_time = timezone.now()
        publish("events/today", json.dumps(eventcache), retain=True)


def event_list_web(request):
    return render(request, 'cbeamd/event_list.django', {'event_list': event_list(request)})
