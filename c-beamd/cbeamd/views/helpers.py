# -*- coding: utf-8 -*-
"""
Shared helpers and utilities for views.
"""

import csv
import json
import logging
import os
import random
import re
import smtplib
import ssl
import string
import traceback
from datetime import date, datetime, timedelta
from email.mime.text import MIMEText
from random import choice
from threading import Timer
from urllib.request import urlopen

import cbeamdcfg as cfg
import feedparser
import paho.mqtt.client as paho
import requests
from django.http import HttpResponse, JsonResponse
from django.shortcuts import get_object_or_404, render
from django.template import Context, loader
from django.utils import timezone
from ics import Calendar

from .. import models
from ..tools.ddate import DDate
from ..tools.handTranslate import HandTranslate
from ..tools.LEDStripe import *

# cerebrum was originally a ServiceProxy that was commented out in views.py
# cerebrum = ServiceProxy('http://c-leuse.cbrp3.c-base.org:7777/')
cerebrum = None

logger = logging.getLogger(__name__)
hysterese = 15
eta_timeout = 120

# mqtt = paho.Client("c-beam")  # Temporarily disabled for testing
mqttserver = "127.0.0.1"

artefact_base_url = "http://[2a02:f28:4::6b39:2d00]/artefact/"

newarrivallist = {}
newetalist = {}
newactivities = []
achievements = {}

eventcache = []
eventdetailcache = []
eventcache_time = timezone.now() - timedelta(days=1)
event_details = []

artefactcache = {}
artefactcache_time = timezone.now() - timedelta(days=1)

cerebrum_state = {}
cerebrum_state['nerdctrl'] = {}

hwstorage_state = "closed"

default_stripe_pattern = 4
default_stripe_speed = 3
default_stripe_offset = 0

# mission states
mission_open = "open"
mission_assigned = "assigned"
mission_completed = "completed"

c_out_volume = 0

hand = HandTranslate()


def AddPadding(data, interrupt, pad, block_size):
    new_data = ''.join([data, interrupt])
    new_data_len = len(new_data)
    remaining_len = block_size - new_data_len
    to_pad_len = remaining_len % block_size
    pad_string = pad * to_pad_len
    return ''.join([new_data, pad_string])


def StripPadding(data, interrupt, pad):
    return data.rstrip(pad).rstrip(interrupt)


def reply(request, text):
    if request.path.startswith('/rpc'):
        return text
    else:
        return HttpResponse(text)


def getuser(user):
    user = user.lower().rstrip()
    if user == "nielc":
        user = "keiner"
    if user == "azt":
        user = "pille"
    try:
        u = models.User.objects.get(username=user)
    except Exception:
        u = models.User(username=user, logintime=timezone.now() - timedelta(seconds=hysterese), extendtime=timezone.now() - timedelta(
            seconds=hysterese), logouttime=timezone.now() - timedelta(seconds=hysterese), status="unknown")
        u.save()
    return u


def getuser_eta(user):
    user = user.lower().rstrip()
    if user == "nielc":
        user = "keiner"
    if user == "azt":
        user = "pille"
    try:
        u = models.User.objects.get(username=user)
    except Exception:
        return None
    return u


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


def publish(topic, payload, retain=False):
    try:
        mqtt.username_pw_set(cfg.mqtt_client_name, password=cfg.mqtt_client_password)
        if cfg.mqtt_server_tls:
            mqtt.tls_set(cfg.mqtt_server_cert, cert_reqs=ssl.CERT_OPTIONAL)
            mqtt.connect(cfg.mqtt_server, port=1884)
        else:
            mqtt.connect(cfg.mqtt_server, port=1883)

        mqtt.publish(topic, payload, qos=1, retain=retain)

    except Exception as e:
        logger.error(e)
        pass


def log_stats():
    from .models import UserStatsEntry
    now = timezone.now()
    entry, created = UserStatsEntry.objects.get_or_create(date=now.date())
    entry.count += 1
    entry.save()


def get_stats():
    from .models import UserStatsEntry
    return list(UserStatsEntry.objects.all().values())


def get_prices():
    prices = []
    with open('preise.csv', 'r') as csvfile:
        pricereader = csv.reader(csvfile, delimiter=';', quotechar='"')
        for row in pricereader:
            prices.append(row)
    return prices


def create_random_password(length):
    chars = string.letters + string.digits
    return ''.join(choice(chars) for _ in range(length))


def send_mail(recipient, text):
    msg = MIMEText(text)
    msg['Subject'] = 'c-beam passwort gesetzt / c-beam password has been set'
    msg['From'] = "c-beam@c-base.org"
    msg['To'] = recipient

    s = smtplib.SMTP('localhost')
    s.sendmail("c-beam@c-base.org", [recipient], msg.as_string())
    s.quit()

    return "aye"
