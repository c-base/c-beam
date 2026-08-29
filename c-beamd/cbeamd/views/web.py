# -*- coding: utf-8 -*-
"""
HTML front-end views.

Split out of the original views.py; function bodies are unchanged.
"""


from django.contrib.auth.decorators import login_required
from django.http import HttpResponse
from django.shortcuts import get_object_or_404, render
from django.template import Context, loader
from ..json_rpc_client import jsonrpc_method

from ..forms import UserForm
from ..models import ActivityLog, User
from ..tools.LEDStripe import *

from .helpers import logger
from .helpers import getuser

def index2(request):
    online_users_list = User.objects.filter(status="online").order_by('username')
    eta_list = User.objects.filter(status="eta").order_by('username')
    t = loader.get_template('cbeamd/index.django')
    c = Context({
        'online_users_list': online_users_list,
        "eta_list": eta_list,
    })
    return HttpResponse(t.render(c))


@login_required
def index(request):
    logger.error("FOOOOOOOOOOOOO")
    user_list_online = User.objects.filter(status="online").order_by('username')
    user_list_eta = User.objects.filter(status="eta").order_by('username')
    user_list_offline = User.objects.filter(status="offline").order_by('username')
    al = ActivityLog.objects.order_by('-timestamp')[:20]
    rev = list(al)
    rev.reverse()
    return render(request, 'cbeamd/index.django', {'user_list_online': user_list_online, 'user_list_eta': user_list_eta, 'user_list_offline': user_list_offline, 'status': 'all', 'activitylog': rev})


@login_required
def user(request, user_id):
    u = get_object_or_404(User, pk=user_id)
    return render(request, 'cbeamd/user_detail.django', {'user': u})


@login_required
def user_online(request):
    user_list = User.objects.filter(status="online").order_by('username')
    return render(request, 'cbeamd/user_list.django', {'user_list': user_list, 'status': 'online'})


@login_required
def user_offline(request):
    user_list = User.objects.filter(status="offline").order_by('username')
    return render(request, 'cbeamd/user_list.django', {'user_list': user_list, 'status': 'offline'})


@login_required
def user_eta(request):
    user_list = User.objects.filter(status="eta").order_by('username')
    return render(request, 'cbeamd/user_list.django', {'user_list': user_list, 'status': 'eta'})


@login_required
def user_all(request):
    user_list_online = User.objects.all().order_by('username')
    return render(request, 'cbeamd/user_list.django', {'user_list': user_list, 'status': 'all'})


@login_required
def user_list_web(request):
    user_list_online = User.objects.filter(status="online").order_by('username')
    user_list_eta = User.objects.filter(status="eta").order_by('username')
    user_list_offline = User.objects.filter(status="offline").order_by('username')
    return render(request, 'cbeamd/user_list.django', {'user_list_online': user_list_online, 'user_list_eta': user_list_eta, 'user_list_offline': user_list_offline, 'status': 'all'})


@jsonrpc_method('user_list')
def user_list(request):
    users = User.objects.all().order_by('username')
    return [user.dic() for user in users]


@jsonrpc_method('stats_list')
def stats_list(request):
    user_list = sorted(list(User.objects.filter(stats_enabled=True).exclude(ap=0)), key=lambda x: x.calc_ap(), reverse=True)
    return [user.dic() for user in user_list]


@login_required
def stats(request):
    user_list = sorted(list(User.objects.filter(stats_enabled=True).exclude(ap=0)), key=lambda x: x.calc_ap(), reverse=True)
    return render(request, 'cbeamd/stats.django', {'user_list': [user.dic() for user in user_list]})


@login_required
def control(request):
    return render(request, 'cbeamd/control.django', {})


@login_required
def c_leuse(request):
    return render(request, 'cbeamd/c_leuse.django', {})


@login_required
def c_buttons(request):
    return render(request, 'cbeamd/c_buttons.django', {})


@login_required
def profile_edit(request):
    if request.method == "POST":
        u = getuser(request.user.username)
        form = UserForm(request.POST, instance=u)
        if form.is_valid():
            form.save()
    else:
        u = getuser(request.user.username)
        form = UserForm(instance=u)
    return render(request, 'cbeamd/user_form.django', locals())
