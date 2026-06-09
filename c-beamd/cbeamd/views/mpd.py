# -*- coding: utf-8 -*-
"""
MPD (Music Player Daemon) control views.
"""

import json
from django.http import HttpResponse

from ..json_rpc_client import jsonrpc_method, ajax
from mpd import MPDClient as RealMPDClient


class MPDClient():
    def __init__(self, host='localhost'):
        self.host = host

    def __enter__(self):
        self.client = RealMPDClient()
        self.client.timeout = 10
        self.client.connect(self.host, 6600)
        return self.client

    def __exit__(self, type, value, traceback):
        self.client.close()
        self.client.disconnect()


def mpd_volume(request, host):
    with MPDClient(host) as client:
        if request.method == 'GET':
            result = {'volume': client.status()['volume']}
        elif request.method == 'POST':
            result = client.setvol(42)

    return HttpResponse(json.dumps(result), content_type="application/json")


@ajax
def mpd_status(request, host):
    result = None
    with MPDClient(host) as client:
        result = client.status()
        result['current_song'] = client.currentsong()
        if 'title' not in result['current_song'].keys():
            result['current_song']['title'] = 'unknown'
        result['playlist'] = client.playlist()
        elapsed = 0
        total = 0
        if 'time' in result.keys():
            (elapsed, total) = result['time'].split(':')
            result['elapsed'] = elapsed
            result['total'] = total
        else:
            result['elapsed'] = 0
            result['total'] = 0
    resp = {"status": 200, "statusText": "OK", "content": result}
    return HttpResponse(json.dumps(resp), content_type="application/json")


def mpd_play(request, host):
    with MPDClient(host) as client:
        result = client.play()
        return HttpResponse(json.dumps(result), content_type="application/json")


def mpd_stop(request, host):
    with MPDClient(host) as client:
        result = client.stop()
        return HttpResponse(json.dumps(result), content_type="application/json")


def mpd_command(request, host, command):
    result = {}
    with MPDClient(host) as client:
        if command == 'play':
            result = client.play()
        elif command == 'pause':
            result = client.pause()
        elif command == 'stop':
            result = client.stop()
        elif command == 'next':
            result = client.next()
        elif command == 'previous':
            result = client.previous()
        elif command == 'backward':
            result = client.seekcur("-10")
        elif command == 'forward':
            result = client.seekcur("+10")
        elif command == 'random':
            result = client.random(abs(mpd_get_random(host) - 1))
        elif command == 'repeat':
            result = client.repeat(abs(mpd_get_repeat(host) - 1))
        elif command == 'vol_up':
            result = client.setvol(mpd_get_volume(host) + 5)
        elif command == 'vol_down':
            result = client.setvol(mpd_get_volume(host) - 5)
    return HttpResponse(json.dumps(result), content_type="application/json")


def mpd_get_random(host):
    result = 0
    with MPDClient(host) as client:
        result = int(client.status()['random'])
    return result


def mpd_get_repeat(host):
    result = 0
    with MPDClient(host) as client:
        result = int(client.status()['repeat'])
    return result


def mpd_get_volume(host):
    result = 0
    with MPDClient(host) as client:
        result = int(client.status()['volume'])
    return result


@ajax
def mpd_listplaylists(request, host):
    result = {}
    with MPDClient(host) as client:
        result = client.listplaylists()
    return result
