"""Replacement authentication decorators that work around redirection loops"""

try:
    from functools import wraps
except ImportError:
    from django.utils.functional import wraps

from django.contrib.auth import REDIRECT_FIELD_NAME
from django.http import HttpResponseForbidden

__all__ = ['permission_required', 'user_passes_test']

def user_passes_test(test_func, login_url=None,
                     redirect_field_name=REDIRECT_FIELD_NAME):
    """Replacement for django.contrib.auth.decorators.user_passes_test that
    returns 403 Forbidden if the user is already logged in.
    """

    def decorator(view_func):
        @wraps(view_func)
        def wrapper(request, *args, **kwargs):
            if test_func(request.user):
                return view_func(request, *args, **kwargs)
            else:
                return HttpResponseForbidden('<h1>Permission denied</h1>')
        return wrapper
    return decorator


def login_required(function=None, redirect_field_name=REDIRECT_FIELD_NAME):
    """Replacement for django.contrib.auth.decorators.login_required that
    returns 403 Forbidden if the user is already logged in.
    """

    actual_decorator = user_passes_test(
        lambda u: u.is_authenticated(),
        redirect_field_name=redirect_field_name
    )
    if function:
        return actual_decorator(function)
    return actual_decorator


def permission_required(perm, login_url=None):
    """Replacement for django.contrib.auth.decorators.permission_required that
    returns 403 Forbidden if the user is already logged in.
    """

    return user_passes_test(lambda u: u.has_perm(perm), login_url=login_url)
