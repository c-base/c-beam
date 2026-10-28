"""
Push notifications (FCM, historically GCM).

Split out of missions.py; function bodies are unchanged.
"""


from django.conf import settings
from django.utils import timezone
from ..json_rpc_client import jsonrpc_method
from pyfcm import FCMNotification

from ..models import Subscription, User

from .helpers import getuser, logger


def _push_service():
    """
    an FCMNotification for the configured service account. pyfcm opens the
    file lazily, so this performs no i/o and the path is only checked on send.
    """
    return FCMNotification(settings.FCM_SERVICE_ACCOUNT_FILE, settings.FCM_PROJECT_ID)


@jsonrpc_method('gcm_register')
def gcm_register(request, user, regid):
    s = Subscription()
    s.regid = regid
    s.user = getuser(user)
    s.save()
    return "aye"


@jsonrpc_method('gcm_update')
def gcm_update(request, user, regid):
    u = getuser(user)
    subs = Subscription.objects.filter(user=u)
    if len(subs) < 1:
        s = Subscription()
        s.regid = regid
        s.user = u
        s.save()
    else:
        s = subs[0]
        s.regid = regid
        s.save()
    return "aye"


@jsonrpc_method('fcm_update')
def fcm_update(request, user, regid):
    u = getuser(user)
    logger.error("fcm_update called: %s - %s", user, regid)
    subs = Subscription.objects.filter(user=u)
    if len(subs) < 1:
        s = Subscription()
        s.regid = regid
        s.user = u
        s.save()
    else:
        s = subs[0]
        s.regid = regid
        s.save()
    return "aye"


# This method should usually not be exposed through JSON-RPC
# @jsonrpc_method('gcm_send')
def gcm_send(request, title, text):
    logger.error("gcm_Send called: %s - %s", title, text)
    logger.critical("gcm_Send called: %s - %s", title, text)
    push_service = _push_service()
    if title == "now boarding":
        users = User.objects.filter(push_boarding=True)
    elif title == "ETA":
        users = User.objects.filter(push_eta=True)
    elif title == "mission completed":
        users = User.objects.filter(push_missions=True, stats_enabled=True)
    else:
        users = []
        logger.errors("users is empty")
        return
    now = timezone.localtime(timezone.now())
    timestamp = "%d:%d" % (now.hour, now.minute)
    subscriptions = Subscription.objects.filter(user__in=users)
    regids = [subscription.regid for subscription in subscriptions]
    data = {'title': title, 'text': text, 'timestamp': timestamp}
    logger.error(data)
    response = None
    try:
        params_list =[{"fcm_token": fcm_token, "data_payload": data} for fcm_token in regids]
        response = push_service.async_notify_multiple_devices(params_list)
        logger.error(response)
    except Exception as e:
        logger.exception(e)
    logger.error(">>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>RESPONSE: %s", response)
    return response


def gcm_send_mission(request, title, text):
    push_service = _push_service()
    users = User.objects.filter(stats_enabled=True, push_missions=True)
    now = timezone.localtime(timezone.now())
    timestamp = "%d:%d" % (now.hour, now.minute)
    subscriptions = Subscription.objects.filter(user__in=users)
    regids = [subscription.regid for subscription in subscriptions]
    data = {'title': title, 'text': text, 'timestamp': timestamp}
    params_list =[{"fcm_token": fcm_token, "data_payload": data} for fcm_token in regids]
    response = push_service.async_notify_multiple_devices(params_list)
    return response


@jsonrpc_method('gcm_send_test')
def gcm_send_test(request, title, text, username):
    push_service = _push_service()
    u = getuser(username)
    now = timezone.localtime(timezone.now())
    timestamp = "%d:%d" % (now.hour, now.minute)
    subscriptions = Subscription.objects.filter(user=u)
    regids = [subscription.regid for subscription in subscriptions]
    data = {'title': title, 'text': text, 'timestamp': timestamp}
    params_list =[{"fcm_token": fcm_token, "data_payload": data} for fcm_token in regids]
    response = push_service.async_notify_multiple_devices(params_list)
    return response
