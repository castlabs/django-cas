__author__ = 'sannies'

from django.conf.urls.defaults import patterns, url


urlpatterns = patterns('django_cas.views',
    url(r'^login$', "login", name="cas_login"),
    url(r'^logout$', "logout", name="cas_logout"),
    url(r'^proxycallback$', "proxy_callback", name="cas_proxy_callback"),

)
