"""CAS login/logout replacement views"""

from urllib import urlencode
from urlparse import urljoin

from django.http import get_host, HttpResponseRedirect, HttpResponseForbidden
from django.conf import settings
from django.contrib.auth import REDIRECT_FIELD_NAME

__all__ = ['login', 'logout']

def _service_url(request, redirect_to=None):
    """Generates application service URL for CAS"""

    protocol = ('http://', 'https://')[request.is_secure()]
    host = get_host(request)
    service = protocol + host + request.path
    if redirect_to:
        if '?' in service:
            service += '&'
        else:
            service += '?'
        service += urlencode({REDIRECT_FIELD_NAME: redirect_to})
    return service


def _redirect_url(request):
    """Redirects to referring page, or CAS_REDIRECT_URL if no referrer is
    set.
    """

    next = request.GET.get(REDIRECT_FIELD_NAME)
    if not next:
        if settings.CAS_IGNORE_REFERER:
            next = settings.CAS_REDIRECT_URL
        else:
            next = request.META.get('HTTP_REFERER', settings.CAS_REDIRECT_URL)
        prefix =  (('http://', 'https://')[request.is_secure()] +
                   get_host(request))
        if next.startswith(prefix):
            next = next[len(prefix):]
    return next


def _login_url(service):
    """Generates CAS login URL"""

    params = {'service': service}
    url = urljoin(settings.CAS_SERVER_URL, 'login') + '?' + urlencode(params)
    return url


def _logout_url(request, next_page=None):
    """Generates CAS logout URL"""

    url = urljoin(settings.CAS_SERVER_URL, 'logout')
    if next_page:
        protocol = ('http://', 'https://')[request.is_secure()]
        host = get_host(request)
        url += '?' + urlencode({'url': protocol + host + next_page})
    return url


def login(request, next_page=None):
    """Forwards to CAS login URL or verifies CAS ticket"""

    if not next_page:
        next_page = _redirect_url(request)
    if request.user.is_authenticated():
        message = "You are logged in as %s." % request.user.username
        request.user.message_set.create(message=message)
        return HttpResponseRedirect(next_page)
    ticket = request.GET.get('ticket')
    service = _service_url(request, next_page)
    if ticket:
        from django.contrib.auth import authenticate, login
        user = authenticate(ticket=ticket, service=service)
        if user is not None:
            login(request, user)
            name = user.first_name or user.username
            message = "Login succeeded. Welcome, %s." % name
            user.message_set.create(message=message)
            return HttpResponseRedirect(next_page)
        else:
            error = "<h1>Forbidden</h1><p>Login failed.</p>"
            return HttpResponseForbidden(error)
    else:
        url = _login_url(service)
        return HttpResponseRedirect(url)


def logout(request, next_page=None):
    """Redirects to CAS logout page"""

    from django.contrib.auth import logout
    logout(request)
    if not next_page:
        next_page = _redirect_url(request)
    if settings.CAS_LOGOUT_COMPLETELY:
        return HttpResponseRedirect(_logout_url(request, next_page))
    else:
        return HttpResponseRedirect(next_page)
