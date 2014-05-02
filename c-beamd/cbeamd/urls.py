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
    url(r'^$', 'cbeamd.views.index'),
    url(r'^stats$', 'cbeamd.views.stats'),
    url(r'^profile$', 'cbeamd.views.profile_edit'),
    url(r'^activitylog$', 'cbeamd.views.activitylog_web'),
    url(r'^activitylog/(?P<activitylog_id>\d+)$', 'cbeamd.views.activitylog_details_web'),
    url(r'^activitylog/(?P<activitylog_id>\d+)/postcomment$', 'cbeamd.views.activitylog_post_comment'),
    url(r'^activitylog/deletecomment/(?P<comment_id>\d+)$', 'cbeamd.views.activitylog_delete_comment'),
    #url(r'^activitylog/(?P<activitylog_id>\d+)/thanks$', 'cbeamd.views.not_implemented'),
    #url(r'^activitylog/(?P<activitylog_id>\d+)/protest$', 'cbeamd.views.not_implemented'),
    url(r'^activitylog_json$', 'cbeamd.views.activitylog_json'),
    #url(r'^cbeamd/', include('cbeamd.foo.urls')),

    # Uncomment the admin/doc line below to enable admin documentation:
    # url(r'^admin/doc/', include('django.contrib.admindocs.urls')),

    # Uncomment the next line to enable the admin:

    url(r'^admin/', include(admin.site.urls)),
    #url(r'^user/(?P<user_id>\d+)/$', 'cbeamd.views.user'),
    url(r'^user/(?P<object_id>\d+)/$', 'django.views.generic.list_detail.object_detail', dict(user_dict, template_name='cbeamd/user_detail.django'), user_dict),
    url(r'^user/(?P<user>\d+)/login$', 'cbeamd.views.login_with_id'),
    url(r'^user/online$', 'cbeamd.views.user_list_web'),
    url(r'^user/offline$', 'cbeamd.views.user_offline'),
    url(r'^user/eta$', 'cbeamd.views.user_eta'),
    url(r'^user/all$', 'cbeamd.views.user_all'),
    url(r'^user/login/(?P<user>.+)$', 'cbeamd.views.login'),
    url(r'^user/logout/(?P<user>.+)$', 'cbeamd.views.logout'),
    url(r'^login$', 'cbeamd.views.auth_login'),
    url(r'^logout$', 'cbeamd.views.auth_logout'),
    url(r'^logactivity$', 'cbeamd.views.logactivity_web'),
    #url(r'^missions/(?P<object_id>\d+)/$', 'django.views.generic.list_detail.object_detail', dict(mission_dict, template_name='cbeamd/mission_detail.django'), mission_dict),
    url(r'^missions$', 'cbeamd.views.mission_list'),
    url(r'^missions/(?P<mission_id>\d+)/edit$', 'cbeamd.views.edit_mission'),
    url(r'^missions/(?P<mission_id>\d+)/assign$', 'cbeamd.views.mission_assign_web'),
    url(r'^missions/(?P<mission_id>\d+)/complete$', 'cbeamd.views.mission_complete_web'),
    url(r'^missions/(?P<mission_id>\d+)/cancel$', 'cbeamd.views.mission_cancel_web'),
    url(r'^artefacts$', 'cbeamd.views.artefact_list_web'),
    url(r'^events$', 'cbeamd.views.event_list_web'),
    #url(r'^stripe/$', 'cbeamd.views.stripe_view'),
    url(r'^control/set_stripe_pattern/(?P<pattern_id>\d+)/$', 'cbeamd.views.set_stripe_pattern_web'),
    url(r'^control/set_stripe_speed/(?P<speed>\d+)/$', 'cbeamd.views.set_stripe_speed_web'),
    url(r'^c_leuse/set_stripe_pattern/(?P<pattern_id>\d+)/$', 'cbeamd.views.set_stripe_pattern_web'),
    url(r'^c_leuse/set_stripe_speed/(?P<speed>\d+)/$', 'cbeamd.views.set_stripe_speed_web'),
    url(r'^control$', 'cbeamd.views.control'),
    url(r'^c_leuse$', 'cbeamd.views.c_leuse'),
    url(r'^c_buttons$', 'cbeamd.views.c_buttons'),
    url(r'^control/softwareendlager$', 'cbeamd.views.hwstorage_web'),
    url(r'^c_buttons/softwareendlager$', 'cbeamd.views.hwstorage_web'),
    url(r'^c_buttons/login$', 'cbeamd.views.login_web'),
    url(r'^c_buttons/logout$', 'cbeamd.views.logout_web'),
    url(r'^c_out$', 'cbeamd.views.c_out_web'),
    url(r'^c_out/play/(?P<sound>.+)$', 'cbeamd.views.c_out_play_web'),
    url(r'^activitylog/', 'cbeamd.views.not_implemented'),
    url(r'^c_out_volume$', 'cbeamd.views.c_out_volume_web'),
    url(r'^c_out_volume_json$', 'cbeamd.views.c_out_volume_json'),
    url(r'^c_out_volume_set/(?P<volume>\d+)$', 'cbeamd.views.c_out_volume_set'),
    url(r'^burningman$', 'cbeamd.views.toggle_burningman'),
    url(r'^nerdctrl$', 'cbeamd.views.nerdctrl'),
    url(r'^weather$', 'cbeamd.views.weather'),
    url(r'^bvg$', 'cbeamd.views.bvg'),
    url(r'^sensors$', 'cbeamd.views.dash'),
    url(r'^dash$', 'cbeamd.views.dash'),
    url(r'^ceitloch$', 'cbeamd.views.ceitlochclocc'),
    url(r'^donut$', 'cbeamd.views.donut'),
    url(r'^reddit$', 'cbeamd.views.reddit'),
    url(r'^welcome/(?P<user>.+)$', 'cbeamd.views.welcome'),
)

urlpatterns += patterns('', (r'^rpc/', jsonrpc_site.dispatch))

