"""CAS authentication middleware"""

import os
from urllib import urlencode

from django.http import HttpResponseRedirect, HttpResponseForbidden
from django.conf import settings
from django.contrib.auth import REDIRECT_FIELD_NAME
from django.contrib.auth.views import login, logout
from django.core.urlresolvers import reverse

from django_cas.views import login as cas_login, logout as cas_logout

__all__ = ['CASMiddleware']

class CASMiddleware(object):
    """Middleware that allows CAS authentication on admin pages"""

    def process_request(self, request):
        """Checks that the authentication middleware is installed"""

        error = ("The Django CAS middleware requires authentication "
                 "middleware to be installed. Edit your MIDDLEWARE_CLASSES "
                 "setting to insert 'django.contrib.auth.middleware."
                 "AuthenticationMiddleware'.")
        assert hasattr(request, 'user'), error

    def process_view(self, request, view_func, view_args, view_kwargs):
        """Forwards unauthenticated requests to the admin page to the CAS
        login URL, as well as calls to django.contrib.auth.views.login and
        logout.
        """

        if view_func == login:
            return cas_login(request, *view_args, **view_kwargs)
        elif view_func == logout:
            return cas_logout(request, *view_args, **view_kwargs)

        admin_prefix = settings.CAS_ADMIN_PREFIX
        if admin_prefix:
            if not request.path.startswith(admin_prefix):
                return None
        else:
            admin_path = ['django', 'contrib', 'admin', 'views']
            try:
                view_file = view_func.func_code.co_filename
            except AttributeError:
                # If we get a protected decorator that abstracts this away
                # into something like _CheckLogin
                view_file = view_func.view_func.func_code.co_filename

            view_path = os.path.split(view_file)[0].split(os.path.sep)[-4:]
            if view_path != admin_path:
                return None

        if request.user.is_authenticated():
            if request.user.is_staff:
                return None
            else:
                error = ('<h1>Forbidden</h1><p>You do not have staff '
                         'privileges.</p>')
                return HttpResponseForbidden(error)
        params = urlencode({REDIRECT_FIELD_NAME: request.get_full_path()})
        url = reverse(cas_login)
        return HttpResponseRedirect(url + '?' + params)
