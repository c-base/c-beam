"""
c-game activity log.

Split out of the original views.py; function bodies are unchanged.
"""

import json

from django.contrib.auth.decorators import login_required
from django.http import HttpResponse
from django.shortcuts import render
from django.views.decorators.csrf import csrf_exempt
from ..json_rpc_client import jsonrpc_method

from ..forms import ActivityLogCommentForm, LogActivityForm
from ..models import Activity, ActivityLog, ActivityLogComment
from ..tools.LEDStripe import *

from . import helpers
from .helpers import getuser


@jsonrpc_method('activitylog')
def activitylog(request):
    """
    returns the current c-game activitylog
    """
    al = ActivityLog.objects.order_by('-timestamp')[:40]
    rev = list(al)
    rev.reverse()
    return [ale.dic() for ale in rev]


@login_required
def activitylog_web(request):
    al = ActivityLog.objects.order_by('-timestamp')[:40]
    rev = list(al)
    rev.reverse()
    return render(request, 'cbeamd/activitylog.django', {'activitylog': rev})


@login_required
def activitylog_details_web(request, activitylog_id):
    activitylog = ActivityLog.objects.get(id=activitylog_id)
    return render(request, 'cbeamd/activitylog_details.django', locals())


@csrf_exempt
@login_required
def logactivity_web(request):
    u = getuser(request.user.username)
    if request.method == 'POST':
        form = LogActivityForm(request.POST)
        if form.is_valid():
            act = form.cleaned_data["activity"]
            ap = form.cleaned_data["ap"]
            logactivity(request, request.user.username, act, ap)
            return render(request, 'cbeamd/activitylog.django', {'form': form, 'result': 'SUCCESS'})
    # else:
        # form = StripeForm()
        # return render(request, 'cbeamd/stripe_form.django', {'form': form})

    return render(request, 'cbeamd/activitylog.django', {'result': 'FAIL'})


@jsonrpc_method('logactivity')
def logactivity(request, user, activity, ap):
    """
    log an activity for user with the description activity and ap activity points
    """
    u = getuser(user)
    # u.ap = u.ap + ap
    if not u.stats_enabled:
        return "stats disabled for user"
    al = ActivityLog()
    al.user = u
    al.ap = int(ap)
    if activity == "login":
        al.activity = Activity.objects.get(activity_type="login")
    elif activity == "logout":
        al.activity = Activity.objects.get(activity_type="logout")
    else:
        act = Activity()
        act.activity_type = "custom"
        act.activity_text = activity
        act.save()
        al.activity = act
    al.save()
    u.ap = u.calc_ap()
    u.save()
    helpers.newactivities.append(al)
    return "aye"


@login_required
def activitylog_json(request):
    al = ActivityLog.objects.order_by('-timestamp')[:40]
    rev = list(al)
    rev.reverse()
    return HttpResponse(json.dumps([ale.dic() for ale in rev]), content_type="application/json")


def not_implemented(request):
    return render(request, 'cbeamd/not_implemented.django', {})


@login_required
def activitylog_post_comment(request, activitylog_id):
    result = "WTF"
    if request.method == 'POST':
        form = ActivityLogCommentForm(request.POST)
        activitylog = ActivityLog.objects.get(id=activitylog_id)
        u = getuser(request.user.username)
        users = [comment.user.username for comment in activitylog.comments.all()]
        if u.username in users:
            result = "commentar connte nicht gespeichert werden, du hast diese aktivita:t bereits commentiert"
        else:
            alc = ActivityLogComment()

            if form.is_valid():
                alc.comment = form.cleaned_data["comment"]
                alc.user = u
                if form.cleaned_data["protest"] == "protest":
                    activitylog.protests += 1
                    alc.comment_type = "protest"
                elif form.cleaned_data["thanks"] == "thanks":
                    activitylog.thanks += 1
                    alc.comment_type = "thanks"
                alc.save()
                activitylog.comments.add(alc)
                activitylog.save()
                result = "dance fu:r deinen commentar"
    return render(request, 'cbeamd/activitylog_details.django', locals())


@login_required
def activitylog_delete_comment(request, comment_id):
    alc = ActivityLogComment.objects.get(id=comment_id)
    u = getuser(request.user.username)
    if alc.user == u:
        alc.delete()
