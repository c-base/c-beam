"""
Shared state, constants and helper functions used across the view modules.

Split out of the original views.py; function bodies are unchanged.
"""

import csv
import logging
import smtplib
import ssl
import string
from datetime import timedelta
from email.mime.text import MIMEText
from random import choice

import cbeamdcfg as cfg
from paho.mqtt import publish as mqtt_publish
from django.http import HttpResponse
from django.utils import timezone
from ..json_rpc_client import JSONRPCClient, jsonrpc_method

from ..models import User, UserStatsEntry
from ..tools.handTranslate import HandTranslate
from ..tools.LEDStripe import *

logger = logging.getLogger(__name__)
hysterese = 15
eta_timeout = 120

# TODO: move strings to settings
mqttserver = "127.0.0.1"
# clients for the collaborating c-base services. these replace the ServiceProxy
# objects from the removed django-json-rpc package; JSONRPCClient is the
# in-tree replacement and is lazy, so constructing one performs no i/o.
#
# note the semantic difference: ServiceProxy handed back the whole JSON-RPC
# envelope, so call sites indexed ['result']. JSONRPCClient unwraps it and
# returns the payload directly - the two call sites that did that have been
# adjusted.
def _service(url):
    """a JSONRPCClient for url, or None when the url is blank (client disabled)."""
    if not url:
        return None
    return JSONRPCClient(url, timeout=cfg.service_timeout)


cout = _service(cfg.cout_url)
ampelrpc = _service(cfg.ampelrpc_url)
nerdctrl_cout = _service(cfg.nerdctrl_cout_url)
cerebrum = _service(cfg.cerebrum_url)
monitord = _service(cfg.monitord_url)
c_leuse_c_out = _service(cfg.c_leuse_c_out_url)
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
        u = User.objects.get(username=user)
    except Exception:
        u = User(username=user, logintime=timezone.now() - timedelta(seconds=hysterese), extendtime=timezone.now() - timedelta(
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
        u = User.objects.get(username=user)
    except Exception:
        return None
    return u


def is_logged_in(user):
    if user == "nielc":
        user = "keiner"
    if user == "azt":
        user = "pille"
    return len(User.objects.filter(username=user, status="online")) > 0


def userlist():
    return [str(user) for user in User.objects.filter(status="online").order_by('username')]


def userlist_with_online_percentage():
    return [str(user) + " (" + user.online_percentage() + "%)" for user in User.objects.filter(status="online").order_by('username')]


@jsonrpc_method('log_stats')
def log_stats():
    u = UserStatsEntry()
    u.usercount = len(User.objects.filter(status="online"))
    u.etacount = len(User.objects.filter(status="eta"))
    u.save()
    return str(u)


@jsonrpc_method('get_stats')
def get_stats(request):
    """
    returns the currents user stats
    """
    return str(UserStatsEntry.objects.all())


def publish(topic, payload, retain=False):
    """
    publish one station-state message to the c-base mqtt broker.

    uses paho's one-shot helper, which connects, flushes the message and
    disconnects again. the previous implementation reconnected a single shared
    client on every call and never disconnected it, and had been dead entirely
    since the module-level client was commented out.
    """
    if not cfg.mqtt_enabled:
        logger.debug("mqtt disabled, dropping publish to %s", topic)
        return

    auth = {'username': cfg.mqtt_client_name}
    if cfg.mqtt_client_password:
        auth['password'] = cfg.mqtt_client_password

    tls = None
    port = 1883
    if cfg.mqtt_server_tls:
        tls = {'ca_certs': cfg.mqtt_server_cert, 'cert_reqs': ssl.CERT_OPTIONAL}
        port = 1884

    try:
        mqtt_publish.single(
            topic, payload, qos=1, retain=retain,
            hostname=cfg.mqtt_server, port=port, auth=auth, tls=tls,
        )
    except Exception:
        # station state is best effort - a broker outage must not fail the
        # request, but it should be visible in the log rather than silent
        logger.warning("mqtt publish to %s failed", topic, exc_info=True)


def create_random_password(length):
    chars = string.ascii_letters + string.digits
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


def get_prices():
    prices = []
    with open('preise.csv', 'r') as csvfile:
        pricereader = csv.reader(csvfile, delimiter=';', quotechar='"')
        for row in pricereader:
            prices.append(row)
    return prices
