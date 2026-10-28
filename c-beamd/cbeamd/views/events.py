"""
c-base event feed views.

Split out of the original views.py. update_event_cache() reads the ics export
with icalendar/recurring_ical_events so that recurring events are expanded.
"""

import json
import re
from datetime import datetime
from urllib.request import urlopen

import feedparser
from django.shortcuts import render
from django.utils import timezone
import icalendar
import recurring_ical_events
from ..json_rpc_client import jsonrpc_method


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
    try:
        update_event_cache()
    except:
        pass
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


def _hhmm(value):
    """
    "1900" for a datetime, "0000" for an all-day event's date. aware datetimes
    are shown in the station's local time, whatever zone the feed used.
    """
    if isinstance(value, datetime):
        if timezone.is_aware(value):
            value = timezone.localtime(value)
        return value.strftime("%H%M")
    return "0000"


def todays_events(ical, today):
    """
    the events that start on `today` according to the ics feed `ical` (bytes),
    as (summaries, details): summaries are the "title (start-end)" strings for
    the events topic, details the dicts for event_list.

    recurring events (RRULE) are expanded, with EXDATE and RECURRENCE-ID
    honoured, so that a monthly stammtisch shows up on its day and not only on
    the day the series was created.
    """
    calendar = icalendar.Calendar.from_ical(ical)
    occurrences = []
    for entry in recurring_ical_events.of(calendar).at(today):
        begin = entry['DTSTART'].dt
        begin_date = begin.date() if isinstance(begin, datetime) else begin
        if begin_date != today:
            continue
        end = entry['DTEND'].dt if 'DTEND' in entry else begin
        title = str(entry.get('SUMMARY') or '-').replace("c   user", "c++ user")
        description = entry.get('DESCRIPTION')
        occurrences.append({
            'id': str(entry.get('UID', 42)),
            'title': title,
            'start': _hhmm(begin),
            'end': _hhmm(end),
            'description': str(description) if description is not None else None,
        })
    occurrences.sort(key=lambda e: (e['start'], e['title']))
    events = ['%s (%s-%s)' % (e['title'], e['start'], e['end']) for e in occurrences]
    return events, occurrences


def update_event_cache():
    if helpers.eventcache_time.day == timezone.now().day:
        return
    url = 'https://www.c-base.org/calendar/exported/c-base-events.ics'
    events, event_details = todays_events(urlopen(url).read(), timezone.localdate())
    helpers.eventcache = events
    helpers.eventdetailcache = event_details
    helpers.eventcache_time = timezone.now()
    publish("events/today", json.dumps(helpers.eventcache), retain=True)


def event_list_web(request):
    return render(request, 'cbeamd/event_list.django', {'event_list': event_list(request)})
