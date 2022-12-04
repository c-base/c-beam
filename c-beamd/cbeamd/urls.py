# from django.conf.urls import patterns, include, url
from django.urls import include, re_path
from .models import User
from .models import Mission
from jsonrpc import jsonrpc_site
from . import views  # you must import the views that need connected
from django.conf import settings
from django.conf.urls.static import static
from django.contrib.auth import views as auth_views
from django.urls import include, path
from rest_framework import routers

router = routers.DefaultRouter()
router.register(r'users', views.UserViewSet)
router.register(r'member', views.MemberViewSet, basename='Member')
router.register(r'prices', views.PriceViewSet, basename='Prices')
router.register(r'events', views.EventViewSet, basename='Events')
router.register(r'barstatus', views.BarViewSet, basename='Barstatus')

from django.contrib import admin
admin.autodiscover()

mission_dict = {
    'queryset': Mission.objects.all(),
}
user_dict = {
    'queryset': User.objects.all(),
}

urlpatterns = [
    re_path(r'^$', views.index, name='index'),
    re_path(r'^stats$', views.stats, name='stats'),
    re_path(r'^profile$', views.profile_edit, name='profile_edit'),
    re_path(r'^activitylog$', views.activitylog_web, name='activitylog_web'),
    re_path(r'^activitylog/(?P<activitylog_id>\d+)$', views.activitylog_details_web, name='activitylog_details_web'),
    re_path(r'^activitylog/(?P<activitylog_id>\d+)/postcomment$', views.activitylog_post_comment, name='activitylog_post_comment'),
    re_path(r'^activitylog/deletecomment/(?P<comment_id>\d+)$', views.activitylog_delete_comment, name='activitylog_delete_comment'),
    # re_path(r'^activitylog/(?P<activitylog_id>\d+)/thanks$, views.not_implemented'),
    # re_path(r'^activitylog/(?P<activitylog_id>\d+)/protest$, views.not_implemented'),
    re_path(r'^activitylog_json$', views.activitylog_json, name='activitylog_json'),
    re_path(r'^mechblast_json$', views.mechblast_json, name='mechblast_json'),

    re_path(r'^admin/', admin.site.urls),
    # re_path(r'^rpc/browse/', jsonrpc.views.browse, name='jsonrpc_browser'),
    re_path(r'^rpc/', jsonrpc_site.dispatch, name="jsonrpc_mountpoint"),
    # re_path(r'^user/(?P<user_id>\d+)/$', views.user),
    # re_path(r'^user/(?P<object_id>\d+)/$', 'django.views.generic.list_detail.object_detail', dict(user_dict, template_name='user_detail.django'), user_dict),
    re_path(r'^user/online$', views.user_list_web, name='user_list_web'),
    re_path(r'^user/offline$', views.user_offline, name='user_offline'),
    re_path(r'^user/eta$', views.user_eta, name='user_eta'),
    re_path(r'^user/all$', views.user_all, name='user_all'),
    # re_path(r'^user/login/(?P<user>.+)$', views.login, name='login'),
    # re_path(r'^user/logout/(?P<user>.+)$', views.logout, name='logout'),
    # re_path(r'^user/(?P<user>\d+)/login$', views.login_with_id, name='login_with_id'),
    # re_path(r'^login$', views.auth_login, name='auth_login'),
    # re_path(r'^logout$', views.auth_logout, name='auth_logout'),
    re_path(r'^login/$', auth_views.LoginView.as_view(template_name="cbeamd/login.django"), name='login'),
    re_path(r'^logout/$', auth_views.LogoutView.as_view(template_name="cbeamd/logout.django"), name='logout'),
    re_path(r'^logactivity$', views.logactivity_web, name='logactivity_web'),
    # re_path(r'^missions/(?P<object_id>\d+)/$', 'django.views.generic.list_detail.object_detail, dict(mission_dict, template_name='mission_detail.django'), mission_dict),
    re_path(r'^missions$', views.mission_list, name='mission_list'),
    re_path(r'^missions/(?P<mission_id>\d+)/edit$', views.edit_mission, name='edit_mission'),
    re_path(r'^missions/(?P<mission_id>\d+)/assign$', views.mission_assign_web, name='mission_assign_web'),
    re_path(r'^missions/(?P<mission_id>\d+)/complete$', views.mission_complete_web, name='mission_complete_web'),
    re_path(r'^missions/(?P<mission_id>\d+)/cancel$', views.mission_cancel_web, name='mission_cancel_web'),
    re_path(r'^artefacts$', views.artefact_list_web, name='artefact_list_web'),
    re_path(r'^events$', views.event_list_web, name='event_list_web'),
    # re_path(r'^stripe/$', views.stripe_view'),
    re_path(r'^control/set_stripe_pattern/(?P<pattern_id>\d+)/$', views.set_stripe_pattern_web, name='set_stripe_pattern'),
    re_path(r'^control/set_stripe_speed/(?P<speed>\d+)/$', views.set_stripe_speed_web, name='set_stripe_speed'),
    re_path(r'^c_leuse/set_stripe_pattern/(?P<pattern_id>\d+)/$', views.set_stripe_pattern_web, name='set_stripe_pattern_web'),
    re_path(r'^c_leuse/set_stripe_speed/(?P<speed>\d+)/$', views.set_stripe_speed_web, name='set_stripe_speed_web'),
    re_path(r'^control$', views.control, name='control'),
    re_path(r'^c_leuse$', views.c_leuse, name='c_leuse'),
    re_path(r'^c_buttons$', views.c_buttons, name='c_buttons'),
    re_path(r'^control/softwareendlager$', views.hwstorage_web, name='hwstorage_web'),
    re_path(r'^c_buttons/softwareendlager$', views.hwstorage_web, name='hwstorage_web_c'),
    re_path(r'^c_buttons/login$', views.login_web, name='login_web'),
    re_path(r'^c_buttons/logout$', views.logout_web, name='logout_web'),
    re_path(r'^c_out$', views.c_out_web, name='c_out_web'),
    re_path(r'^c_out/play/(?P<sound>.+)$', views.c_out_play_web, name='c_out_play_web'),
    re_path(r'^activitylog/', views.not_implemented, name='not_implemented'),
    re_path(r'^c_out_volume$', views.c_out_volume_web, name='c_out_volume_web'),
    re_path(r'^c_out_volume_json$', views.c_out_volume_json, name='c_out_volume_json'),
    re_path(r'^c_out_volume_set/(?P<volume>\d+)$', views.c_out_volume_set, name='c_out_volume_set'),
    re_path(r'^burningman$', views.toggle_burningman, name='toggle_burningman'),
    re_path(r'^nerdctrl$', views.nerdctrl, name='nerdctrl'),
    re_path(r'^c-beam-viewer$', views.cbeamviewer, name='cbeamviewer'),
    re_path(r'^weather$', views.weather, name='weather'),
    re_path(r'^bvg$', views.bvg, name='bvg'),
    re_path(r'^sensors$', views.dash, name='sensors'),
    re_path(r'^mechdisplay$', views.mechdisplay, name='mechdisplay'),
    re_path(r'^he1display$', views.he1display, name='he1display'),
    re_path(r'^dash$', views.dash, name='dash'),
    re_path(r'^ceitloch$', views.ceitlochclocc, name='ceitlochclocc'),
    re_path(r'^donut$', views.donut, name='donut'),
    re_path(r'^reddit$', views.reddit, name='reddit'),
    re_path(r'^welcome/(?P<user>.+)$', views.welcome, name='welcome'),
    re_path(r'^control/ampel/(?P<location>.+)/(?P<color>.+)/(?P<state>\d)/$', views.ampel, name='ampel'),
    re_path(r'^mpd/(?P<host>.+)/volume/$', views.mpd_volume, name='mpd_volume'),
    re_path(r'^mpd/(?P<host>.+)/mpd_listplaylists/$', views.mpd_listplaylists, name='mpd_listplaylists'),
    re_path(r'^mpd/(?P<host>.+)/status/$', views.mpd_status, name='mpd_status'),
    re_path(r'^mpd/(?P<host>.+)/command/(?P<command>\w+)/$', views.mpd_command, name='mpd_command'),
    path('api/', include(router.urls)),
    path('api-auth/', include('rest_framework.urls', namespace='rest_framework'))
] + static(settings.STATIC_URL, document_root=settings.STATIC_ROOT)
