# -*- coding: utf-8 -*-
"""
Activity log views.
"""

import json
from datetime import timedelta

from django.contrib.auth.decorators import login_required
from django.http import HttpResponse
from django.shortcuts import render
from django.utils import timezone
from django.views.decorators.csrf import csrf_exempt

from .. import models
from ..forms import ActivityLogCommentForm, LogActivityForm
from ..json_rpc_client import jsonrpc_method
from .view_helpers import getuser, newactivities, publish


@jsonrpc_method('activitylog')
def activitylog(request):
    """
    returns the current c-game activitylog
    """
    al = models.ActivityLog.objects.order_by('-timestamp')[:40]
    rev = list(al)
    rev.reverse()
    return [ale.dic() for ale in rev]


@login_required
def activitylog_web(request):
    al = models.ActivityLog.objects.order_by('-timestamp')[:40]
    rev = list(al)
    rev.reverse()
    return render(request, 'cbeamd/activitylog.django', {'activitylog': rev})


@login_required
def activitylog_details_web(request, activitylog_id):
    activitylog = models.ActivityLog.objects.get(id=activitylog_id)
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

    return render(request, 'cbeamd/activitylog.django', {'result': 'FAIL'})


@jsonrpc_method('logactivity')
def logactivity(request, user, activity, ap):
    """
    log an activity for user with the description activity and ap activity points
    """
    global newactivities
    u = getuser(user)
    al = models.ActivityLog()
    al.user = u
    al.activity = models.Activity.objects.get(activity_type=activity)
    al.ap = ap
    al.timestamp = timezone.now()
    al.save()
    newactivities.append(al.notification_str())
    publish("activitylog/new", al.notification_str())
    return "aye"


def activitylog_json(request):
    al = models.ActivityLog.objects.order_by('-timestamp')[:40]
    rev = list(al)
    rev.reverse()
    return HttpResponse(json.dumps([ale.dic() for ale in rev]), content_type="application/json")


def not_implemented(request):
    return "not implemented"


@csrf_exempt
@login_required
def activitylog_post_comment(request, activitylog_id):
    activitylog = models.ActivityLog.objects.get(id=activitylog_id)
    if request.method == 'POST':
        form = ActivityLogCommentForm(request.POST)
        if form.is_valid():
            comment = form.save(commit=False)
            comment.activitylog = activitylog
            comment.user = getuser(request.user.username)
            comment.save()
    else:
        form = ActivityLogCommentForm()
    return render(request, 'cbeamd/activitylog_details.django', locals())


@login_required
def activitylog_delete_comment(request, comment_id):
    comment = models.ActivityLogComment.objects.get(id=comment_id)
    activitylog = comment.activitylog
    comment.delete()
    return render(request, 'cbeamd/activitylog_details.django', locals())
