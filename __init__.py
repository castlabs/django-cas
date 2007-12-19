from urllib import urlopen, urlencode
from urlparse import urljoin

from django.conf import settings

defaults = {'CAS_SERVER_URL': None,
            'CAS_POPULATE_USER': None,
            'CAS_ADMIN_PREFIX': None,
            'CAS_LOGIN_URL': '/accounts/login/',
            'CAS_LOGOUT_URL': '/accounts/logout/',
            'CAS_REDIRECT_URL': '/',
            'CAS_REDIRECT_FIELD_NAME': 'next',
            }

for key, value in defaults.iteritems():
    try:
        getattr(settings, key)
    except AttributeError:
        setattr(settings, key, value)

def get_populate_callback(callback):
    if callable(callback):
        return callback
    try:
        dot = callback.rindex('.')
    except ValueError:
        from django.core import exceptions
        error = "Error importing CAS_POPULATE_USER callback: %s" % callback
        raise exceptions.ImproperlyConfigured(error)
    module_name, func_name = callback[:dot], callback[dot + 1:]
    module = __import__(module_name, {}, {}, [''])
    try:
        func = getattr(module, func_name)
    except AttributeError:
        from django.core import exceptions
        error = "Error importing CAS_POPULATE_USER callback: %s" % callback
        raise exceptions.ImproperlyConfigured(error)
    assert callable(func)
    return func

def populate_user(user):
    if settings.CAS_POPULATE_USER:
        callback = get_populate_callback(settings.CAS_POPULATE_USER)
        return callback(user)

def service_url(request, redirect_to=None):
    from django.http import get_host
    host = get_host(request)
    protocol = request.is_secure() and 'https://' or 'http://'
    service = protocol + host + request.path
    if redirect_to:
        if '?' in service:
            service += '&'
        else:
            service += '?'
        service += urlencode({settings.CAS_REDIRECT_FIELD_NAME: redirect_to})
    return service

def redirect_url(request):
    next = request.GET.get(settings.CAS_REDIRECT_FIELD_NAME)
    if not next:
        next = request.META.get('HTTP_REFERER', settings.CAS_REDIRECT_URL)
    return next

def login_url(service):
    params = {'service': service}
    url = urljoin(settings.CAS_SERVER_URL, 'login') + '?' + urlencode(params)
    if settings.DEBUG: print "Logging in: %s" % url
    return url

def validate_url():
    return urljoin(settings.CAS_SERVER_URL, 'validate')

def verify(ticket, service):
    params = {'ticket': ticket, 'service': service}
    url = validate_url() + '?' + urlencode(params)
    if settings.DEBUG: print "Verifying ticket: %s" % url
    page = urlopen(url)
    verified = page.readline().strip()
    username = page.readline().strip()
    if verified == 'yes':
        return username
    return None