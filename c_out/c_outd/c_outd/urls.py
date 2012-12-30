from django.conf.urls import patterns, include, url
from jsonrpc import jsonrpc_site
import views

# Uncomment the next two lines to enable the admin:
# from django.contrib import admin
# admin.autodiscover()

urlpatterns = patterns('',
    # Examples:
    # url(r'^$', 'c_outd.views.home', name='home'),
    # url(r'^c_outd/', include('c_outd.foo.urls')),

    # Uncomment the admin/doc line below to enable admin documentation:
    # url(r'^admin/doc/', include('django.contrib.admindocs.urls')),

    # Uncomment the next line to enable the admin:
    # url(r'^admin/', include(admin.site.urls)),
)

urlpatterns += patterns('', (r'^rpc/', jsonrpc_site.dispatch))
