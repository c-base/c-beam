# -*- coding: utf-8 -*-
"""
Web page rendering views.
"""

from django.contrib.auth.decorators import login_required
from django.shortcuts import render

from .helpers import models, getuser
from .user import userlist, userlist_with_online_percentage


@login_required
def index2(request):
    return render(request, 'cbeamd/index.django', {
        'userlist': userlist(),
        'userlist_with_online_percentage': userlist_with_online_percentage()
    })


@login_required
def index(request):
    return render(request, 'cbeamd/index.django', {
        'userlist': userlist(),
        'userlist_with_online_percentage': userlist_with_online_percentage()
    })


@login_required
def user(request):
    return render(request, 'cbeamd/user.django', {'userlist': userlist()})


@login_required
def user_online(request):
    return render(request, 'cbeamd/user_online.django', {'userlist': userlist()})


@login_required
def user_offline(request):
    return render(request, 'cbeamd/user_offline.django', {'userlist': userlist()})


@login_required
def user_eta(request):
    from .eta import etalist
    return render(request, 'cbeamd/user_eta.django', {'etalist': etalist()})


@login_required
def user_all(request):
    return render(request, 'cbeamd/user_all.django', {'userlist': userlist()})


@login_required
def user_list_web(request):
    return render(request, 'cbeamd/user_list.django', {
        'userlist': userlist(),
        'userlist_with_online_percentage': userlist_with_online_percentage()
    })


@login_required
def user_list(request):
    return render(request, 'cbeamd/user_list.django', {'userlist': userlist()})


@login_required
def stats_list(request):
    from .helpers import get_stats
    return render(request, 'cbeamd/stats_list.django', {'stats': get_stats()})


@login_required
def stats(request):
    from .helpers import get_stats
    return render(request, 'cbeamd/stats.django', {'stats': get_stats()})


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
    from ..forms import UserForm
    if request.method == "POST":
        u = getuser(request.user.username)
        form = UserForm(request.POST, instance=u)
        if form.is_valid():
            form.save()
    else:
        u = getuser(request.user.username)
        form = UserForm(instance=u)
    return render(request, 'cbeamd/user_form.django', locals())
