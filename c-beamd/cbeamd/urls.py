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
    url(r'^$', 'cbeamd.views.user_online'),
    url(r'^stats$', 'cbeamd.views.stats'),
    url(r'^activitylog$', 'cbeamd.views.activitylog'),
    #url(r'^cbeamd/', include('cbeamd.foo.urls')),

    # Uncomment the admin/doc line below to enable admin documentation:
    # url(r'^admin/doc/', include('django.contrib.admindocs.urls')),

    # Uncomment the next line to enable the admin:

    url(r'^admin/', include(admin.site.urls)),
    #url(r'^user/(?P<user_id>\d+)/$', 'cbeamd.views.user'),
    url(r'^user/(?P<object_id>\d+)/$', 'django.views.generic.list_detail.object_detail', dict(user_dict, template_name='cbeamd/user_detail.django'), user_dict),
    url(r'^user/(?P<user>\d+)/login$', 'cbeamd.views.login_with_id'),
    url(r'^user/online$', 'cbeamd.views.user_online'),
    url(r'^user/offline$', 'cbeamd.views.user_offline'),
    url(r'^user/eta$', 'cbeamd.views.user_eta'),
    url(r'^user/all$', 'cbeamd.views.user_all'),
    url(r'^user/login/(?P<user>.+)$', 'cbeamd.views.login'),
    url(r'^user/logout/(?P<user>.+)$', 'cbeamd.views.logout'),
    url(r'^login$', 'cbeamd.views.auth_login'),
    url(r'^logout$', 'cbeamd.views.auth_logout'),
    #url(r'^missions/(?P<object_id>\d+)/$', 'django.views.generic.list_detail.object_detail', dict(mission_dict, template_name='cbeamd/mission_detail.django'), mission_dict),
    url(r'^missions$', 'cbeamd.views.mission_list'),
    url(r'^missions/(?P<object_id>\d+)/edit$', 'cbeamd.views.edit_mission'),
    url(r'^artefacts$', 'cbeamd.views.artefact_list_web'),
    url(r'^events$', 'cbeamd.views.event_list_web'),
    #url(r'^stripe/$', 'cbeamd.views.stripe_view'),
    url(r'^control/set_stripe_pattern/(?P<pattern_id>\d+)/$', 'cbeamd.views.set_stripe_pattern_web'),
    url(r'^control/set_stripe_speed/(?P<speed>\d+)/$', 'cbeamd.views.set_stripe_speed_web'),
    url(r'^control$', 'cbeamd.views.control'),
    url(r'^control/softwareendlager$', 'cbeamd.views.hwstorage_web'),
    url(r'^c_out$', 'cbeamd.views.c_out_web'),
    url(r'^c_out/play/(?P<sound>.+)$', 'cbeamd.views.c_out_play_web'),
)

urlpatterns += patterns('', (r'^rpc/', jsonrpc_site.dispatch))

