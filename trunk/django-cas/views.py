from django.http import HttpResponseRedirect, HttpResponseForbidden, urlencode
from django.conf import settings
from django_cas import redirect_url, service_url

def login(request, next_page=None):
    if not next_page:
        next_page = redirect_url(request)
    if request.user.is_authenticated():
        message = "You are logged in as %s." % request.user.username
        request.user.message_set.create(message=message)
        return HttpResponseRedirect(next_page)
    ticket = request.GET.get('ticket')
    service = service_url(request, next_page)
    if ticket:
        from django.contrib.auth import authenticate, login
        user = authenticate(ticket=ticket, service=service)
        if user is not None:
            login(request, user)
            name = user.first_name or user.username
            message = "Login succeeded. Welcome, %s." % name
            user.message_set.create(message=message)
            if settings.DEBUG:
                print "Please welcome %s to the system." % user
            return HttpResponseRedirect(next_page)
        else:
            error = "<h1>Forbidden</h1><p>Login failed.</p>"
            return HttpResponseForbidden(error)
    else:
        url = login_url(service)
        return HttpResponseRedirect(url)

def logout(request, next_page=None):
    from django.contrib.auth import logout
    logout(request)
    if not next_page:
        next_page = redirect_url(request)
    return HttpResponseRedirect(next_page)