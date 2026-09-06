"""
c-base event feed views.

Split out of the original views.py; function bodies are unchanged.
"""

import json
import re
from datetime import date
from urllib.request import urlopen

import feedparser
from django.shortcuts import render
from django.utils import timezone
from ics import Calendar
from ..json_rpc_client import jsonrpc_method

from ..tools.LEDStripe import *

from . import helpers
from .helpers import publish

#################################################################
# event methods
#################################################################

@jsonrpc_method('events')
def events(request):
    """
    get todays events
    """
    update_event_cache()
    return helpers.eventcache


@jsonrpc_method('event_list')
def event_list(request):
    """
    get todays events with details
    """
    update_event_cache()
    return helpers.eventdetailcache


@jsonrpc_method('event_detail')
def event_detail(request, id):
    """
    get details for event with id id
    """
    d = feedparser.parse('http://www.c-base.org/calender/phpicalendar/rss/rss2.0.php?cal=&cpath=&rssview=today')
    # d = feedparser.parse('https://www.c-base.org/calender/phpicalendar/rss/rss2.0.php?cal=&cpath=&rssview=month')
    for entry in d['entries']:
        title = re.search(r'.*: (.*)', entry['title']).group(1)
        end = re.search(r'(\d\d\d\d-\d\d-\d\d)T(\d\d:\d\d):(\d\d)', entry['ev_enddate']).group(2).replace(':', '')
        start = re.search(r'(\d\d\d\d-\d\d-\d\d)T(\d\d:\d\d):(\d\d)', entry['ev_startdate']).group(2).replace(':', '')
        title = title.replace("c   user", "c++ user")
        # events.append('%s (%s-%s)' % (title, start, end))
    return "aye"


def update_event_cache():
    if helpers.eventcache_time.day == timezone.now().day:
        return
    events = []
    event_details = []
    # try:
    # d = feedparser.parse('https://www.c-base.org/calendar/exported/c-base-events.ics')
    # d = feedparser.parse('https://www.c-base.org/calender/phpicalendar/rss/rss2.0.php?cal=&cpath=&rssview=month')
    # d = feedparser.parse('http://www.c-base.org/calender/phpicalendar/rss/rss2.0.php?cal=&cpath=&rssview=today')
    # except:
    # pass

    url = 'https://www.c-base.org/calendar/exported/c-base-events.ics'
    c = Calendar(urlopen(url).read().decode('utf-8'))

    if c is not None:
        for entry in c.events:  # d['entries']:
            entryid = 42
            try:
                # entryid = re.search(r'.*&uid=(.*)@google.com', entry['id']).group(1)
                entryid = entry.uid  # re.search(r'.*&uid=(.*)', entry['id']).group(1)
            except Exception:
                pass

            title = entry.name  # re.search(r'.*: (.*)', entry['title']).group(1)
            end = re.search(r'(\d\d\d\d-\d\d-\d\d)T(\d\d:\d\d):(\d\d)', str(entry.end)).group(2).replace(':', '')
            start = re.search(r'(\d\d\d\d-\d\d-\d\d)T(\d\d:\d\d):(\d\d)', str(entry.begin)).group(2).replace(':', '')
            #start = re.search(r'(\d\d\d\d-\d\d-\d\d)T(\d\d:\d\d):(\d\d)', entry['ev_startdate']).group(2).replace(':', '')
            if isinstance(title, str):
                title = title.replace("c   user", "c++ user")
            else:
                title = "-"
            if str(entry.begin).startswith(date.today().strftime("%Y-%m-%d")):
                description = entry.description  # ['summary_detail']['value']
                events.append('%s (%s-%s)' % (title, start, end))
                event_details.append({'id': entryid, 'title': title, 'start': start, 'end': end, 'description': description})
        helpers.eventcache = events
        helpers.eventdetailcache = event_details
        helpers.eventcache_time = timezone.now()
        publish("events/today", json.dumps(helpers.eventcache), retain=True)


def event_list_web(request):
    return render(request, 'cbeamd/event_list.django', {'event_list': event_list(request)})
