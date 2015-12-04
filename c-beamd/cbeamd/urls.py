from django.conf.urls import patterns, include, url
from models import User
from models import Mission
from jsonrpc import jsonrpc_site
import views # you must import the views that need connected

# Uncomment the next two lines to enable the admin:
from django.contrib import admin
admin.autodiscover()

mission_dict = {
            'queryset': Mission.objects.all(),
}
user_dict = {
            'queryset': User.objects.all(),
}

urlpatterns = patterns('',
    # Examples:
    #url(r'^$', 'cbeamd.views.index'),
    url(r'^$', 'cbeamd.views.index', name='index'),
    url(r'^stats$', 'cbeamd.views.stats', name='stats'),
    url(r'^profile$', 'cbeamd.views.profile_edit', name='profile_edit'),
    url(r'^activitylog$', 'cbeamd.views.activitylog_web', name='activitylog_web'),
    url(r'^activitylog/(?P<activitylog_id>\d+)$', 'cbeamd.views.activitylog_details_web', name='activitylog_details_web'),
    url(r'^activitylog/(?P<activitylog_id>\d+)/postcomment$', 'cbeamd.views.activitylog_post_comment', name='activitylog_post_comment'),
    url(r'^activitylog/deletecomment/(?P<comment_id>\d+)$', 'cbeamd.views.activitylog_delete_comment', name='activitylog_delete_comment'),
    #url(r'^activitylog/(?P<activitylog_id>\d+)/thanks$', 'cbeamd.views.not_implemented'),
    #url(r'^activitylog/(?P<activitylog_id>\d+)/protest$', 'cbeamd.views.not_implemented'),
    url(r'^activitylog_json$', 'cbeamd.views.activitylog_json', name='activitylog_json'),
    #url(r'^cbeamd/', include('cbeamd.foo.urls')),

    # Uncomment the admin/doc line below to enable admin documentation:
    # url(r'^admin/doc/', include('django.contrib.admindocs.urls')),

    # Uncomment the next line to enable the admin:

    url(r'^admin/', include(admin.site.urls), name='admin'),
    url(r'^rpc/browse/', 'jsonrpc.views.browse', name='jsonrpc_browser'),
    url(r'^rpc/', jsonrpc_site.dispatch, name="jsonrpc_mountpoint"),
    #url(r'^user/(?P<user_id>\d+)/$', 'cbeamd.views.user'),
    #url(r'^user/(?P<object_id>\d+)/$', 'django.views.generic.list_detail.object_detail', dict(user_dict, template_name='cbeamd/user_detail.django'), user_dict),
    url(r'^user/(?P<user>\d+)/login$', 'cbeamd.views.login_with_id', name='login_with_id'),
    url(r'^user/online$', 'cbeamd.views.user_list_web', name='user_list_web'),
    url(r'^user/offline$', 'cbeamd.views.user_offline', name='user_offline'),
    url(r'^user/eta$', 'cbeamd.views.user_eta', name='user_eta'),
    url(r'^user/all$', 'cbeamd.views.user_all', name='user_all'),
    url(r'^user/login/(?P<user>.+)$', 'cbeamd.views.login', name='login'),
    url(r'^user/logout/(?P<user>.+)$', 'cbeamd.views.logout', name='logout'),
    url(r'^login$', 'cbeamd.views.auth_login', name='auth_login'),
    url(r'^logout$', 'cbeamd.views.auth_logout', name='auth_logout'),
    url(r'^logactivity$', 'cbeamd.views.logactivity_web', name='logactivity_web'),
    #url(r'^missions/(?P<object_id>\d+)/$', 'django.views.generic.list_detail.object_detail', dict(mission_dict, template_name='cbeamd/mission_detail.django'), mission_dict),
    url(r'^missions$', 'cbeamd.views.mission_list', name='mission_list'),
    url(r'^missions/(?P<mission_id>\d+)/edit$', 'cbeamd.views.edit_mission', name='edit_mission'),
    url(r'^missions/(?P<mission_id>\d+)/assign$', 'cbeamd.views.mission_assign_web', name='mission_assign_web'),
    url(r'^missions/(?P<mission_id>\d+)/complete$', 'cbeamd.views.mission_complete_web', name='mission_complete_web'),
    url(r'^missions/(?P<mission_id>\d+)/cancel$', 'cbeamd.views.mission_cancel_web', name='mission_cancel_web'),
    url(r'^artefacts$', 'cbeamd.views.artefact_list_web', name='artefact_list_web'),
    url(r'^events$', 'cbeamd.views.event_list_web', name='event_list_web'),
    #url(r'^stripe/$', 'cbeamd.views.stripe_view'),
    url(r'^control/set_stripe_pattern/(?P<pattern_id>\d+)/$', 'cbeamd.views.set_stripe_pattern_web', name='set_stripe_pattern'),
    url(r'^control/set_stripe_speed/(?P<speed>\d+)/$', 'cbeamd.views.set_stripe_speed_web', name='set_stripe_speed'),
    url(r'^c_leuse/set_stripe_pattern/(?P<pattern_id>\d+)/$', 'cbeamd.views.set_stripe_pattern_web', name='set_stripe_pattern_web'),
    url(r'^c_leuse/set_stripe_speed/(?P<speed>\d+)/$', 'cbeamd.views.set_stripe_speed_web', name='set_stripe_speed_web'),
    url(r'^control$', 'cbeamd.views.control', name='control'),
    url(r'^c_leuse$', 'cbeamd.views.c_leuse', name='c_leuse'),
    url(r'^c_buttons$', 'cbeamd.views.c_buttons', name='c_buttons'),
    url(r'^control/softwareendlager$', 'cbeamd.views.hwstorage_web', name='hwstorage_web'),
    url(r'^c_buttons/softwareendlager$', 'cbeamd.views.hwstorage_web', name='hwstorage_web_c'),
    url(r'^c_buttons/login$', 'cbeamd.views.login_web', name='login_web'),
    url(r'^c_buttons/logout$', 'cbeamd.views.logout_web', name='logout_web'),
    url(r'^c_out$', 'cbeamd.views.c_out_web', name='c_out_web'),
    url(r'^c_out/play/(?P<sound>.+)$', 'cbeamd.views.c_out_play_web', name='c_out_play_web'),
    url(r'^activitylog/', 'cbeamd.views.not_implemented', name='not_implemented'),
    url(r'^c_out_volume$', 'cbeamd.views.c_out_volume_web', name='c_out_volume_web'),
    url(r'^c_out_volume_json$', 'cbeamd.views.c_out_volume_json', name='c_out_volume_json'),
    url(r'^c_out_volume_set/(?P<volume>\d+)$', 'cbeamd.views.c_out_volume_set', name='c_out_volume_set'),
    url(r'^burningman$', 'cbeamd.views.toggle_burningman', name='toggle_burningman'),
    url(r'^nerdctrl$', 'cbeamd.views.nerdctrl', name='nerdctrl'),
    url(r'^c-beam-viewer$', 'cbeamd.views.cbeamviewer', name='cbeamviewer'),
    url(r'^weather$', 'cbeamd.views.weather', name='weather'),
    url(r'^bvg$', 'cbeamd.views.bvg', name='bvg'),
    url(r'^sensors$', 'cbeamd.views.dash', name='sensors'),
    url(r'^dash$', 'cbeamd.views.dash', name='dash'),
    url(r'^ceitloch$', 'cbeamd.views.ceitlochclocc', name='ceitlochclocc'),
    url(r'^donut$', 'cbeamd.views.donut', name='donut'),
    url(r'^reddit$', 'cbeamd.views.reddit', name='reddit'),
    url(r'^welcome/(?P<user>.+)$', 'cbeamd.views.welcome', name='welcome'),
    url(r'^bar/preise$', 'cbeamd.views.bar_preise', name='bar_preise'),
    url(r'^bar/leergut$', 'cbeamd.views.bar_leergut', name='bar_leergut'),
    url(r'^bar/calc$', 'cbeamd.views.bar_calc', name='bar_Calc'),
    url(r'^bar/abrechnung$', 'cbeamd.views.bar_abrechnung', name='bar_abrechnung'),
    url(r'^control/ampel/(?P<location>.+)/(?P<color>.+)/(?P<state>\d)/$', 'cbeamd.views.ampel', name='ampel'),
)

