#from django.conf.urls import patterns, include, url
from django.conf.urls import url, include
from .models import User
from .models import Mission
from jsonrpc import jsonrpc_site
from . import views # you must import the views that need connected
from django.conf import settings
from django.conf.urls.static import static
from django.contrib.auth import views as auth_views


# Uncomment the next two lines to enable the admin:
from django.contrib import admin
admin.autodiscover()

mission_dict = {
            'queryset': Mission.objects.all(),
}
user_dict = {
            'queryset': User.objects.all(),
}

urlpatterns = [
    url(r'^$', views.index, name='index'),
    url(r'^stats$', views.stats, name='stats'),
    url(r'^profile$', views.profile_edit, name='profile_edit'),
    url(r'^activitylog$', views.activitylog_web, name='activitylog_web'),
    url(r'^activitylog/(?P<activitylog_id>\d+)$', views.activitylog_details_web, name='activitylog_details_web'),
    url(r'^activitylog/(?P<activitylog_id>\d+)/postcomment$', views.activitylog_post_comment, name='activitylog_post_comment'),
    url(r'^activitylog/deletecomment/(?P<comment_id>\d+)$', views.activitylog_delete_comment, name='activitylog_delete_comment'),
    #url(r'^activitylog/(?P<activitylog_id>\d+)/thanks$, views.not_implemented'),
    #url(r'^activitylog/(?P<activitylog_id>\d+)/protest$, views.not_implemented'),
    url(r'^activitylog_json$', views.activitylog_json, name='activitylog_json'),
    url(r'^mechblast_json$', views.mechblast_json, name='mechblast_json'),
    #url(r'^', include('foo.urls')),

    # Uncomment the admin/doc line below to enable admin documentation:
    # url(r'^admin/doc/', include('django.contrib.admindocs.urls')),

    # Uncomment the next line to enable the admin:

    url(r'^admin/', include(admin.site.urls), name='admin'),
    #url(r'^rpc/browse/', jsonrpc.views.browse, name='jsonrpc_browser'),
    url(r'^rpc/', jsonrpc_site.dispatch, name="jsonrpc_mountpoint"),
    #url(r'^user/(?P<user_id>\d+)/$', views.user),
    #url(r'^user/(?P<object_id>\d+)/$', 'django.views.generic.list_detail.object_detail', dict(user_dict, template_name='user_detail.django'), user_dict),
    url(r'^user/online$', views.user_list_web, name='user_list_web'),
    url(r'^user/offline$', views.user_offline, name='user_offline'),
    url(r'^user/eta$', views.user_eta, name='user_eta'),
    url(r'^user/all$', views.user_all, name='user_all'),
    #url(r'^user/login/(?P<user>.+)$', views.login, name='login'),
    #url(r'^user/logout/(?P<user>.+)$', views.logout, name='logout'),
    #url(r'^user/(?P<user>\d+)/login$', views.login_with_id, name='login_with_id'),
    #url(r'^login$', views.auth_login, name='auth_login'),
    #url(r'^logout$', views.auth_logout, name='auth_logout'),
    url(r'^login/$', auth_views.login, { 'template_name': "cbeamd/login.django" }, name='login'),
    url(r'^logout/$', auth_views.logout, {'template_name': 'cbeamd/logout.django'}, name='logout'),
    url(r'^logactivity$', views.logactivity_web, name='logactivity_web'),
    #url(r'^missions/(?P<object_id>\d+)/$', 'django.views.generic.list_detail.object_detail, dict(mission_dict, template_name='mission_detail.django'), mission_dict),
    url(r'^missions$', views.mission_list, name='mission_list'),
    url(r'^missions/(?P<mission_id>\d+)/edit$', views.edit_mission, name='edit_mission'),
    url(r'^missions/(?P<mission_id>\d+)/assign$', views.mission_assign_web, name='mission_assign_web'),
    url(r'^missions/(?P<mission_id>\d+)/complete$', views.mission_complete_web, name='mission_complete_web'),
    url(r'^missions/(?P<mission_id>\d+)/cancel$', views.mission_cancel_web, name='mission_cancel_web'),
    url(r'^artefacts$', views.artefact_list_web, name='artefact_list_web'),
    url(r'^events$', views.event_list_web, name='event_list_web'),
    #url(r'^stripe/$', views.stripe_view'),
    url(r'^control/set_stripe_pattern/(?P<pattern_id>\d+)/$', views.set_stripe_pattern_web, name='set_stripe_pattern'),
    url(r'^control/set_stripe_speed/(?P<speed>\d+)/$', views.set_stripe_speed_web, name='set_stripe_speed'),
    url(r'^c_leuse/set_stripe_pattern/(?P<pattern_id>\d+)/$', views.set_stripe_pattern_web, name='set_stripe_pattern_web'),
    url(r'^c_leuse/set_stripe_speed/(?P<speed>\d+)/$', views.set_stripe_speed_web, name='set_stripe_speed_web'),
    url(r'^control$', views.control, name='control'),
    url(r'^c_leuse$', views.c_leuse, name='c_leuse'),
    url(r'^c_buttons$', views.c_buttons, name='c_buttons'),
    url(r'^control/softwareendlager$', views.hwstorage_web, name='hwstorage_web'),
    url(r'^c_buttons/softwareendlager$', views.hwstorage_web, name='hwstorage_web_c'),
    url(r'^c_buttons/login$', views.login_web, name='login_web'),
    url(r'^c_buttons/logout$', views.logout_web, name='logout_web'),
    url(r'^c_out$', views.c_out_web, name='c_out_web'),
    url(r'^c_out/play/(?P<sound>.+)$', views.c_out_play_web, name='c_out_play_web'),
    url(r'^activitylog/', views.not_implemented, name='not_implemented'),
    url(r'^c_out_volume$', views.c_out_volume_web, name='c_out_volume_web'),
    url(r'^c_out_volume_json$', views.c_out_volume_json, name='c_out_volume_json'),
    url(r'^c_out_volume_set/(?P<volume>\d+)$', views.c_out_volume_set, name='c_out_volume_set'),
    url(r'^burningman$', views.toggle_burningman, name='toggle_burningman'),
    url(r'^nerdctrl$', views.nerdctrl, name='nerdctrl'),
    url(r'^c-beam-viewer$', views.cbeamviewer, name='cbeamviewer'),
    url(r'^weather$', views.weather, name='weather'),
    url(r'^bvg$', views.bvg, name='bvg'),
    url(r'^sensors$', views.dash, name='sensors'),
    url(r'^mechdisplay$', views.mechdisplay, name='mechdisplay'),
    url(r'^he1display$', views.he1display, name='he1display'),
    url(r'^dash$', views.dash, name='dash'),
    url(r'^ceitloch$', views.ceitlochclocc, name='ceitlochclocc'),
    url(r'^donut$', views.donut, name='donut'),
    url(r'^reddit$', views.reddit, name='reddit'),
    url(r'^welcome/(?P<user>.+)$', views.welcome, name='welcome'),
    url(r'^bar/preise$', views.bar_preise, name='bar_preise'),
    url(r'^bar/leergut$', views.bar_leergut, name='bar_leergut'),
    url(r'^bar/calc$', views.bar_calc, name='bar_Calc'),
    url(r'^bar/abrechnung$', views.bar_abrechnung, name='bar_abrechnung'),
    url(r'^control/ampel/(?P<location>.+)/(?P<color>.+)/(?P<state>\d)/$', views.ampel, name='ampel'),
    url(r'^mpd/(?P<host>.+)/volume/$', views.mpd_volume, name='mpd_volume'),
    url(r'^mpd/(?P<host>.+)/mpd_listplaylists/$', views.mpd_listplaylists, name='mpd_listplaylists'),
    url(r'^mpd/(?P<host>.+)/status/$', views.mpd_status, name='mpd_status'),
    url(r'^mpd/(?P<host>.+)/command/(?P<command>\w+)/$', views.mpd_command, name='mpd_command'),
] + static(settings.STATIC_URL, document_root=settings.STATIC_ROOT)
