"""Replacement authentication decorators that work around redirection loops"""

from django.contrib.auth import REDIRECT_FIELD_NAME
from django.contrib.auth.decorators import _CheckLogin
from django.http import HttpResponseForbidden, HttpResponseRedirect

__all__ = ['permission_required', 'user_passes_test']

class CheckLoginOrForbid(_CheckLogin):

    def __call__(self, request, *args, **kwargs):
        if self.test_func(request.user):
            return self.view_func(request, *args, **kwargs)
        else:
            return HttpResponseForbidden('<h1>Permission denied</h1>')


def user_passes_test(test_func, login_url=None,
                     redirect_field_name=REDIRECT_FIELD_NAME):
    """Replacement for django.contrib.auth.decorators.user_passes_test that
    returns 403 Forbidden if the user is already logged in.
    """

    def decorate(view_func):
        return CheckLoginOrForbid(view_func, test_func, login_url,
                                  redirect_field_name)
    return decorate


def permission_required(perm, login_url=None):
    """Replacement for django.contrib.auth.decorators.permission_required that
    returns 403 Forbidden if the user is already logged in.
    """

    return user_passes_test(lambda u: u.has_perm(perm), login_url=login_url)
