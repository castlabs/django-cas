# PERMFAIL Modifications

from django.contrib.auth import REDIRECT_FIELD_NAME
from django.http import HttpResponseRedirect, HttpResponseForbidden
from urllib import quote
from django.conf import settings


FAIL_URL = "/oops"

def authenticated_user_passes_test(test_func, login_url=settings.LOGIN_URL, fail_url=FAIL_URL):
    """
    Decorator for views that checks that the user passes the given test,
    redirecting to the log-in page if necessary. The test should be a callable
    that takes the user object and returns True if the user passes.

    The failure url is for when people need to pass a test but needs a
    response other than being redirected to the login page.

    The auth_required option is there in case your test_function performs
    
    """
    def _dec(view_func):
        def _checklogin(request, *args, **kwargs):
            # import pdb; pdb.set_trace()
            if not request.user.is_authenticated():
                return HttpResponseRedirect('%s?%s=%s' % (login_url, REDIRECT_FIELD_NAME,
                                                          quote(request.get_full_path())))
            if test_func(request.user):
                return view_func(request, *args, **kwargs)
            # We have failed, give us the error page
            error = "<h1>Forbidden</h1><p>You do not have sufficient permissions<p>"
            return HttpResponseForbidden(error)
        _checklogin.__doc__ = view_func.__doc__
        _checklogin.__dict__ = view_func.__dict__

        return _checklogin
    return _dec

def permission_required(perm, login_url=settings.LOGIN_URL, fail_url=FAIL_URL):
    """
    Decorator for views that checks whether a user has a particular permission
    enabled, redirecting to the log-in page if necessary.
    """
    return authenticated_user_passes_test(lambda u: u.has_perm(perm), login_url=login_url,fail_url=fail_url)
