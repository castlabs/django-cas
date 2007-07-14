from os import path
from django.http import HttpResponseRedirect, HttpResponseForbidden, urlencode
from django.conf import settings

class CASMiddleware(object):
    def process_request(self, request):
        error = "The Django CAS middleware requires authentication "
                "middleware to be installed. Edit your MIDDLEWARE_CLASSES "
                "setting to insert 'django.contrib.auth.middleware."
                "AuthenticationMiddleware'."
        assert hasattr(request, 'user'), error
    
    def process_view(self, request, view_func, view_args, view_kwargs):
        admin_prefix = settings.CAS_ADMIN_PREFIX
        if admin_prefix:
            if not request.path.startswith(admin_prefix):
                return None
        else:
            admin_path = ['django', 'contrib', 'admin', 'views']
            view_file = view_func.func_code.co_filename
            view_path = path.split(view_file)[0].split(path.sep)[-4:]
            if view_path != admin_path:
                return None
        if request.user.is_authenticated():
            if request.user.is_staff:
                return None
            else:
                error = "<h1>Forbidden</h1>"
                        "<p>You do not have staff privileges.</p>"
                return HttpResponseForbidden(error)
        field, url = settings.CAS_REDIRECT_FIELD_NAME, settings.CAS_LOGIN_URL
        params = urlencode({field: request.get_full_path()})
        return HttpResponseRedirect(url + '?' + params)