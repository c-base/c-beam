from django.conf.urls import patterns, include, url
from models import User
from jsonrpc import jsonrpc_site
import views # you must import the views that need connected

# Uncomment the next two lines to enable the admin:
from django.contrib import admin
admin.autodiscover()

info_dict = {
            'queryset': User.objects.all(),
}


urlpatterns = patterns('',
    # Examples:
    url(r'^$', 'cbeamd.views.index'),
    #url(r'^cbeamd/', include('cbeamd.foo.urls')),

    # Uncomment the admin/doc line below to enable admin documentation:
    # url(r'^admin/doc/', include('django.contrib.admindocs.urls')),

    # Uncomment the next line to enable the admin:

    url(r'^admin/', include(admin.site.urls)),
    #url(r'^user/(?P<user_id>\d+)/$', 'cbeamd.views.user'),
    (r'^user/(?P<object_id>\d+)/$', 'django.views.generic.list_detail.object_detail', dict(info_dict, template_name='cbeamd/user_detail.django'), info_dict),
    url(r'^user/(?P<user>\d+)/login$', 'cbeamd.views.login_with_id'),
    url(r'^user/online$', 'cbeamd.views.user_online'),
    url(r'^user/offline$', 'cbeamd.views.user_offline'),
    url(r'^user/eta$', 'cbeamd.views.user_eta'),
    url(r'^user/all$', 'cbeamd.views.user_all'),
    url(r'^user/login/(?P<user>.+)$', 'cbeamd.views.login'),
    url(r'^user/logout/(?P<user>.+)$', 'cbeamd.views.logout'),
    url(r'^login$', 'cbeamd.views.auth_login'),
    url(r'^logout$', 'cbeamd.views.auth_logout'),
)

urlpatterns += patterns('', (r'^rpc/', jsonrpc_site.dispatch))

