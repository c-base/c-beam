"""
Mission handling.

Split out of the original views.py; function bodies are unchanged.
"""


from django.contrib.auth.decorators import login_required, user_passes_test
from django.shortcuts import get_object_or_404, render
from ..json_rpc_client import jsonrpc_method

from ..forms import MissionForm
from ..models import Activity, ActivityLog, Mission

from .helpers import mission_assigned, mission_completed, mission_open
from .helpers import getuser, publish
from .push import gcm_send_mission


@jsonrpc_method('add_mission')
def add_mission(request, short_description):
    """
    add a new mission with a short_description
    """
    m = Mission(short_description=short_description)
    m.save()
    return "aye"


@jsonrpc_method('missions')
def missions(request):
    """
    returns a list of available missions
    """
    return [str(mission) for mission in Mission.objects.order_by('status', 'short_description')]


@jsonrpc_method('mission_detail')
def mission_detail(request, mission_id):
    """
    returns the details for the mission specified with mission_id
    """
    mission = get_object_or_404(Mission, pk=mission_id)
    return mission.dic()


@jsonrpc_method('mission_assign')
def mission_assign(request, user, mission_id):
    """
    assign the mission with mission_id to user
    """
    u = getuser(user)
    m = Mission.objects.get(id=mission_id)
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
    m = Mission.objects.get(id=mission_id)
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
    m = Mission.objects.get(id=mission_id)
    if u in m.assigned_to.all() and m.status == mission_assigned:
        # m.assigned_to.clear()
        m.assigned_to.remove(u)
        if m.assigned_to.count() <= 0:
            if m.repeat_after_days == 0:
                m.status = mission_completed
            else:
                m.status = mission_open
        m.save()
        if u.stats_enabled:
            al = ActivityLog()
            al.user = u
            al.ap = m.ap
            al.activity = Activity.objects.get(activity_type="mission completed")
            al.mission = m
            al.save()
            # u.ap = u.ap + m.ap
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
    missions_available = Mission.objects.filter(status="open").order_by('short_description')
    missions_in_progress = Mission.objects.filter(status="assigned").order_by('short_description')
    cuser = getuser(request.user.username),
    result = mission_assign(request, request.user.username, mission_id)
    if result == "success":
        result = "Mission erfolgreich gestartet"
    else:
        result = "Mission konnte nicht gestartet werden"
    return render(request, 'cbeamd/mission_list.django', locals())


@login_required
def mission_complete_web(request, mission_id):
    missions_available = Mission.objects.filter(status="open").order_by('short_description')
    missions_in_progress = Mission.objects.filter(status="assigned").order_by('short_description')
    cuser = getuser(request.user.username),
    result = mission_complete(request, request.user.username, mission_id)
    if result == "success":
        result = "Mission erfolgreich abgeschlossen"
    else:
        result = "Mission konnte nicht abgeschlossen werden"
    return render(request, 'cbeamd/mission_list.django', locals())


@login_required
def mission_cancel_web(request, mission_id):
    missions_available = Mission.objects.filter(status="open").order_by('short_description')
    missions_in_progress = Mission.objects.filter(status="assigned").order_by('short_description')
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
        missions = Mission.objects.order_by('-status', 'short_description')
        return [mission.dic() for mission in missions]
    else:
        missions_available = Mission.objects.filter(status="open").order_by('short_description')
        missions_in_progress = Mission.objects.filter(status="assigned").order_by('short_description')
        cuser = request.user.username
        return render(request, 'cbeamd/mission_list.django', locals())


def is_mission_editor(user):
    return True


@login_required
@user_passes_test(is_mission_editor)
def edit_mission(request, mission_id):
    if request.method == "POST":
        m = Mission.objects.get(pk=mission_id)
        form = MissionForm(request.POST, instance=m)
        if form.is_valid():
            form.save()
            result = "Mission gespeichert"
            return render(request, 'cbeamd/mission_list.django', locals())
            # return HttpResponseRedirect('/missions/%s' % mission_id)
    else:
        m = Mission.objects.get(id=mission_id)
        form = MissionForm(instance=m)
    return render(request, 'cbeamd/mission_form.django', locals())
