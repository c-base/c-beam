# -*- coding: utf-8 -*-
"""
Mission handling and push notification views.
"""

from django.contrib.auth.decorators import login_required
from django.http import HttpResponse
from django.shortcuts import get_object_or_404, render
from django.utils import timezone
from django.views.decorators.http import require_http_methods
from pyfcm import FCMNotification

from .. import models
from ..forms import MissionForm
from ..json_rpc_client import jsonrpc_method
from ..view_helpers import (
    getuser, log_stats, mission_assigned, mission_completed, mission_open, publish
)


@jsonrpc_method('add_mission')
def add_mission(request, short_description):
    """
    add a new mission with a short_description
    """
    m = models.Mission(short_description=short_description)
    m.save()
    return "aye"


@jsonrpc_method('missions')
def missions(request):
    """
    returns a list of available missions
    """
    return [str(mission) for mission in models.Mission.objects.order_by('status', 'short_description')]


@jsonrpc_method('mission_detail')
def mission_detail(request, mission_id):
    """
    returns the details for the mission specified with mission_id
    """
    mission = get_object_or_404(models.Mission, pk=mission_id)
    return mission.dic()


@jsonrpc_method('mission_assign')
def mission_assign(request, user, mission_id):
    """
    assign the mission with mission_id to user
    """
    u = getuser(user)
    m = models.Mission.objects.get(id=mission_id)
    if m.status == mission_open or m.status == mission_assigned:
        m.assigned_to.add(u)
        m.status = mission_assigned
        m.save()
        return "success"
    return "mission not available"


@jsonrpc_method('mission_cancel')
def mission_cancel(request, user, mission_id):
    """
    cancel the mission with mission_id for user
    """
    u = getuser(user)
    m = models.Mission.objects.get(id=mission_id)
    if u in m.assigned_to.all() and m.status == mission_assigned:
        m.assigned_to.remove(u)
        if m.assigned_to.count() <= 0:
            m.status = mission_open
        m.save()
        return "success"
    return "not assigned to user"


@jsonrpc_method('mission_complete')
def mission_complete(request, user, mission_id):
    """
    complete the mission with mission_id for user
    """
    u = getuser(user)
    m = models.Mission.objects.get(id=mission_id)
    if u in m.assigned_to.all() and m.status == mission_assigned:
        m.assigned_to.remove(u)
        if m.assigned_to.count() <= 0:
            if m.repeat_after_days == 0:
                m.status = mission_completed
            else:
                m.status = mission_open
        m.save()
        if u.stats_enabled:
            al = models.ActivityLog()
            al.user = u
            al.ap = m.ap
            al.activity = models.Activity.objects.get(activity_type="mission completed")
            al.mission = m
            al.save()
            u.ap = u.calc_ap()
            u.save()
            if not u.no_google:
                try:
                    gcm_send_mission(request, "mission completed", al.notification_str())
                except Exception:
                    pass
            publish("mission/completed", str(al.notification_str()))

        return "success"
    return "failure"


@login_required
def mission_assign_web(request, mission_id):
    missions_available = models.Mission.objects.filter(status="open").order_by('short_description')
    missions_in_progress = models.Mission.objects.filter(status="assigned").order_by('short_description')
    cuser = getuser(request.user.username),
    result = mission_assign(request, request.user.username, mission_id)
    if result == "success":
        result = "Mission erfolgreich gestartet"
    else:
        result = "Mission konnte nicht gestartet werden"
    return render(request, 'cbeamd/mission_list.django', locals())


@login_required
def mission_complete_web(request, mission_id):
    missions_available = models.Mission.objects.filter(status="open").order_by('short_description')
    missions_in_progress = models.Mission.objects.filter(status="assigned").order_by('short_description')
    cuser = getuser(request.user.username),
    result = mission_complete(request, request.user.username, mission_id)
    if result == "success":
        result = "Mission erfolgreich abgeschlossen"
    else:
        result = "Mission konnte nicht abgeschlossen werden"
    return render(request, 'cbeamd/mission_list.django', locals())


@login_required
def mission_cancel_web(request, mission_id):
    missions_available = models.Mission.objects.filter(status="open").order_by('short_description')
    missions_in_progress = models.Mission.objects.filter(status="assigned").order_by('short_description')
    cuser = getuser(request.user.username),
    result = mission_cancel(request, request.user.username, mission_id)
    if result == "success":
        result = "Mission erfolgreich abgebrochen"
    else:
        result = "Mission konnte nicht abgebrochen"

    return render(request, 'cbeamd/mission_list.django', locals())


# @login_required
@jsonrpc_method('mission_list')
def mission_list(request):
    """
    returns a list of available missions
    """
    if request.path.startswith('/rpc'):
        missions = models.Mission.objects.order_by('-status', 'short_description')
        return [mission.dic() for mission in missions]
    else:
        missions_available = models.Mission.objects.filter(status="open").order_by('short_description')
        missions_in_progress = models.Mission.objects.filter(status="assigned").order_by('short_description')
        cuser = request.user.username
        return render(request, 'cbeamd/mission_list.django', locals())


def is_mission_editor(user):
    return True


@login_required
def edit_mission(request, mission_id):
    if request.method == "POST":
        m = models.Mission.objects.get(pk=mission_id)
        form = MissionForm(request.POST, instance=m)
        if form.is_valid():
            form.save()
            result = "Mission gespeichert"
            return render(request, 'cbeamd/mission_list.django', locals())
    else:
        m = models.Mission.objects.get(id=mission_id)
        form = MissionForm(instance=m)
    return render(request, 'cbeamd/mission_form.django', locals())


@jsonrpc_method('gcm_register')
def gcm_register(request, user, regid):
    s = models.Subscription()
    s.regid = regid
    s.user = getuser(user)
    s.save()
    return "aye"


@jsonrpc_method('gcm_update')
def gcm_update(request, user, regid):
    u = getuser(user)
    subs = models.Subscription.objects.filter(user=u)
    if len(subs) < 1:
        s = models.Subscription()
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
    from .view_helpers import logger
    logger.error("fcm_update called: %s - %s", user, regid)
    subs = models.Subscription.objects.filter(user=u)
    if len(subs) < 1:
        s = models.Subscription()
        s.regid = regid
        s.user = u
        s.save()
    else:
        s = subs[0]
        s.regid = regid
        s.save()
    return "aye"


@jsonrpc_method('gcm_send')
def gcm_send(request, subtype, text):
    import cbeamdcfg as cfg
    from .view_helpers import logger
    api_key = cfg.fcm_server_key
    push_service = FCMNotification(api_key=api_key)

    if subtype == 'ETA':
        registration_ids = []
        for sub in models.Subscription.objects.all():
            if sub.user.etasub and sub.user.push_eta:
                registration_ids.append(sub.regid)
    elif subtype == 'mission':
        registration_ids = []
        for sub in models.Subscription.objects.all():
            if sub.user.push_missions:
                registration_ids.append(sub.regid)
    elif subtype == 'boarding':
        registration_ids = []
        for sub in models.Subscription.objects.all():
            if sub.user.push_boarding:
                registration_ids.append(sub.regid)
    else:
        registration_ids = []
        for sub in models.Subscription.objects.all():
            registration_ids.append(sub.regid)

    if len(registration_ids) > 0:
        try:
            message_body = text
            message_title = "c-beam"

            response = push_service.notify_multiple_device(
                registration_ids=registration_ids,
                message_title=message_title,
                message_body=message_body
            )
            logger.info(response)
        except Exception as e:
            logger.error(e)
            return "error"
    return "aye"


@jsonrpc_method('gcm_send_mission')
def gcm_send_mission(request, subtype, text):
    return gcm_send(request, subtype, text)


@jsonrpc_method('gcm_send_test')
def gcm_send_test(request, user, text):
    u = getuser(user)
    subs = models.Subscription.objects.filter(user=u)
    if len(subs) > 0:
        s = subs[0]
        import cbeamdcfg as cfg
        push_service = FCMNotification(api_key=cfg.fcm_server_key)
        response = push_service.notify_single_device(
            registered_id=s.regid,
            message_title="c-beam test",
            message_body=text
        )
        return response
    return "no registration id"
