"""
Tests for the calendar feed in views/events.py.

The c-base calendar publishes most events as recurring series (a monthly
stammtisch is one VEVENT with an RRULE), so "today's events" has to expand
the recurrences. The feed is never fetched here: todays_events() takes the
ics bytes, and update_event_cache() is run against a patched urlopen.
"""

from datetime import date, timedelta
from unittest.mock import patch

from django.test import SimpleTestCase
from django.utils import timezone

from cbeamd.views import helpers
from cbeamd.views.events import todays_events, update_event_cache

# the last wednesday of october 2026 is the 28th
TODAY = date(2026, 10, 28)

FEED = b"""BEGIN:VCALENDAR
VERSION:2.0
PRODID:-//c-base//test//
BEGIN:VEVENT
SUMMARY:Emacs Stammtisch
DTSTART;TZID=Europe/Berlin:20250129T190000
DTEND;TZID=Europe/Berlin:20250129T230000
RRULE:FREQ=MONTHLY;BYDAY=WE;BYSETPOS=-1
UID:emacs
DESCRIPTION:M-x party
END:VEVENT
BEGIN:VEVENT
SUMMARY:Berlindroid
DTSTART;TZID=Europe/Berlin:20250129T190000
DTEND;TZID=Europe/Berlin:20250129T220000
RRULE:FREQ=MONTHLY;BYDAY=WE;BYSETPOS=-1
UID:droid
END:VEVENT
BEGIN:VEVENT
SUMMARY:Berlindroid (moved)
DTSTART;TZID=Europe/Berlin:20261028T183000
DTEND;TZID=Europe/Berlin:20261028T213000
UID:droid
RECURRENCE-ID;TZID=Europe/Berlin:20261028T190000
END:VEVENT
BEGIN:VEVENT
SUMMARY:c-lounge
DTSTART;TZID=Europe/Berlin:20250130T200000
DTEND;TZID=Europe/Berlin:20250130T234200
RRULE:FREQ=WEEKLY;BYDAY=TH
UID:lounge
END:VEVENT
BEGIN:VEVENT
SUMMARY:Cancelled Stammtisch
DTSTART;TZID=Europe/Berlin:20250129T180000
DTEND;TZID=Europe/Berlin:20250129T190000
RRULE:FREQ=MONTHLY;BYDAY=WE;BYSETPOS=-1
EXDATE;TZID=Europe/Berlin:20261028T180000
UID:cancelled
END:VEVENT
BEGIN:VEVENT
SUMMARY:c   user group
DTSTART:20261028T160000Z
DTEND:20261028T170000Z
UID:cpp
END:VEVENT
BEGIN:VEVENT
SUMMARY:Open Day
DTSTART;VALUE=DATE:20261028
DTEND;VALUE=DATE:20261029
UID:openday
END:VEVENT
BEGIN:VEVENT
SUMMARY:Congress
DTSTART;TZID=Europe/Berlin:20261027T100000
DTEND;TZID=Europe/Berlin:20261029T180000
UID:congress
END:VEVENT
END:VCALENDAR
"""


class TodaysEventsTest(SimpleTestCase):
    def setUp(self):
        self.events, self.details = todays_events(FEED, TODAY)
        self.titles = [d['title'] for d in self.details]

    def test_recurring_series_is_expanded_onto_today(self):
        self.assertIn('Emacs Stammtisch', self.titles)
        self.assertIn('Emacs Stammtisch (1900-2300)', self.events)

    def test_recurrence_id_override_replaces_the_series_instance(self):
        self.assertIn('Berlindroid (moved)', self.titles)
        self.assertNotIn('Berlindroid', self.titles)
        self.assertIn('Berlindroid (moved) (1830-2130)', self.events)

    def test_exdate_cancels_the_instance(self):
        self.assertNotIn('Cancelled Stammtisch', self.titles)

    def test_other_days_are_left_out(self):
        self.assertNotIn('c-lounge', self.titles)

    def test_events_started_on_an_earlier_day_are_left_out(self):
        self.assertNotIn('Congress', self.titles)

    def test_utc_times_are_shown_in_local_time(self):
        # late october: CET, so 16:00Z is 17:00 in berlin
        self.assertIn('c++ user group (1700-1800)', self.events)

    def test_all_day_event(self):
        self.assertIn('Open Day (0000-0000)', self.events)

    def test_sorted_by_start_with_details(self):
        self.assertEqual(self.titles,
                         ['Open Day', 'c++ user group', 'Berlindroid (moved)', 'Emacs Stammtisch'])
        emacs = self.details[-1]
        self.assertEqual(emacs, {'id': 'emacs', 'title': 'Emacs Stammtisch', 'start': '1900',
                                 'end': '2300', 'description': 'M-x party'})
        self.assertIsNone(self.details[0]['description'])

    def test_empty_day(self):
        self.assertEqual(todays_events(FEED, date(2026, 11, 2)), ([], []))


class UpdateEventCacheTest(SimpleTestCase):
    def setUp(self):
        helpers.eventcache = []
        helpers.eventdetailcache = []
        helpers.eventcache_time = timezone.now() - timedelta(days=1)

    def test_fetches_the_feed_and_fills_the_cache(self):
        # a weekly event that started four weeks ago and so recurs today
        today = timezone.localdate()
        dtstart = (today - timedelta(weeks=4)).strftime('%Y%m%d')
        feed = FEED.replace(b'20250130T200000', dtstart.encode() + b'T200000') \
                   .replace(b'20250130T234200', dtstart.encode() + b'T234200') \
                   .replace(b'RRULE:FREQ=WEEKLY;BYDAY=TH', b'RRULE:FREQ=WEEKLY')
        with patch('cbeamd.views.events.urlopen') as urlopen, \
             patch('cbeamd.views.events.publish') as publish:
            urlopen.return_value.read.return_value = feed
            update_event_cache()
        self.assertIn('c-lounge (2000-2342)', helpers.eventcache)
        self.assertEqual(helpers.eventcache_time.date(), today)
        publish.assert_called_once()
        self.assertEqual(publish.call_args.args[0], 'events/today')

    def test_is_refreshed_once_a_day(self):
        helpers.eventcache_time = timezone.now()
        with patch('cbeamd.views.events.urlopen') as urlopen:
            update_event_cache()
        urlopen.assert_not_called()
