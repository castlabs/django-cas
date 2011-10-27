Django CAS
===========

django_cas is a CAS 1.0 and CAS 2.0 authentication backend for Django. It allows you to use Django's built-in authentication mechanisms and User model while adding support for CAS.

It also includes a middleware that intercepts calls to the original login and logout pages and forwards them to the CASified versions, and adds CAS support to the admin interface.

Installation
------------

Run python setup.py install, or place the django_cas directory in your PYTHONPATH directly.
(Note: If you're using Python 2.4 or older, you'll need to install ElementTree to use CAS 2.0 functionality.)

Now add it to the middleware and authentication backends in your settings. Make sure you also have the 
authentication middleware installed. Here's what mine looks like::

    MIDDLEWARE_CLASSES = (
     'django.middleware.common.CommonMiddleware',
     'django.contrib.sessions.middleware.SessionMiddleware',
     'django.contrib.auth.middleware.AuthenticationMiddleware',
     'django_cas.middleware.CASMiddleware',
     'django.middleware.doc.XViewMiddleware',
    )


    AUTHENTICATION_BACKENDS = (
     'django.contrib.auth.backends.ModelBackend',
     'django_cas.backends.CASBackend',
    )

Set the following required setting in settings.py:

* CAS_SERVER_URL: This is the only setting you must explicitly define. Set it to the base URL of your CAS source (e.g. http://sso.some.edu/cas/).

Optional settings include:

* CAS_ADMIN_PREFIX: The URL prefix of the Django administration site. If undefined, the CAS middleware will check the view being rendered to see if it lives in django.contrib.admin.views.
* CAS_EXTRA_LOGIN_PARAMS: Extra URL parameters to add to the login URL when redirecting the user.
* CAS_IGNORE_REFERER: If True, logging out of the application will always send the user to the URL specified by CAS_REDIRECT_URL.
* CAS_LOGOUT_COMPLETELY: If False, logging out of the application won't log the user out of CAS as well.
* CAS_REDIRECT_URL: Where to send a user after logging in or out if there is no referrer and no next page set. Default is /.
* CAS_RETRY_LOGIN: If True and an unknown or invalid ticket is received, the user is redirected back to the login page.
* CAS_VERSION: The CAS protocol version to use. '1' and '2' are supported, with '2' being the default.
* CAS_PROXY_CALLBACK: The URL given to the CAS server in order to initialize a proxy ticket. The ticket granting ticket will be sent to this URL. The url must be registered in urls.py and handled by django_cas.views.proxy_callback, e.g: ``(r'^accounts/login/casProxyCallback$', 'django_cas.views.proxy_callback')``
* CAS_USER_DETAILS_RESOLVER: template method for populating the user object.

Make sure your project knows how to log users in and out by adding these to your URL mappings:

``(r'^accounts/login/$', 'django_cas.views.login'),``
``(r'^accounts/logout/$', 'django_cas.views.logout'),``

Users should now be able to log into your site (and staff into the administration interface) using CAS.

Populating The User Object From CAS 2.0 Attributes
--------------------------------------------------

Since there are manyfold ways transmitting user attributes in CAS and even more ways to map them
 on django.auth.User the mapping is done via a template method.

The template method is defined via the ``CAS_USER_DETAILS_RESOLVER`` setting::

    CAS_USER_DETAILS_RESOLVER = cas_integration.populate_user

and an example method would be::

    CAS_URI = 'http://www.yale.edu/tp/cas'
    NSMAP = {'cas': CAS_URI}
    CAS = '{%s}' % CAS_URI

    def populate_user(user, authentication_response):
        if authentication_response.find(CAS + 'authenticationSuccess/'  + CAS + 'attributes'  , namespaces=NSMAP) is not None:
            attr = authentication_response.find(CAS + 'authenticationSuccess/'  + CAS + 'attributes'  , namespaces=NSMAP)

            if attr.find(CAS + 'is_superuser', NSMAP) is not None:
                user.is_superuser = attr.find(CAS + 'is_superuser', NSMAP).text.upper() == 'TRUE'

            if attr.find(CAS + 'is_staff', NSMAP) is not None:
                user.is_staff = attr.find(CAS + 'is_staff', NSMAP).text.upper() == 'TRUE'
        pass



Preventing Infinite Redirects
-----------------------------
Django's current implementation of its permission_required and user_passes_test decorators (in django.contrib.auth.decorators) has a known issue that can cause users to experience infinite redirects. The decorators return the user to the login page, even if they're already logged in, which causes a loop with SSO services like CAS.

django_cas provides fixed versions of these decorators in django_cas.decorators. Usage is unchanged, and in the event that this issue is fixed, the decorators should still work without issue.

For more information see http://code.djangoproject.com/ticket/4617.

Customizing the 403 Error Page
Django doesn't provide a simple way to customize 403 error pages, so you'll have to make a response middleware that handles HttpResponseForbidden.

For example, in views.py::

    from django.http import HttpResponseForbidden
    from django.template import RequestContext, loader
    
    def forbidden(request, template_name='403.html'):
        """Default 403 handler"""
    
        t = loader.get_template(template_name)
        return HttpResponseForbidden(t.render(RequestContext(request)))

And in middleware.py::

    from django.http import HttpResponseForbidden
    from yourapp.views import forbidden
    
    class Custom403Middleware(object):
        """Catches 403 responses and renders 403.html"""
        def process_response(self, request, response):
            if isinstance(response, HttpResponseForbidden):
                return forbidden(request)
            else:
                return response

Now add yourapp.middleware.Custom403Middleware to your MIDDLEWARE_CLASSES setting and create a template named 403.html.

CAS 2.0 support
---------------
The CAS 2.0 protocol is supported in the same way that 1.0 is; no extensions or new features from the CAS 2.0 specification are implemented. elementtree is required to use this functionality. (elementtree is also included in Python 2.5's standard library.)

Note: The CAS 3.x server uses the CAS 2.0 protocol. There is no CAS 3.0 protocol, though the CAS 3.x server does allow extensions to the protocol.

Differences Between Django CAS 1.0 and 2.0
Version 2.0 of django_cas breaks compatibility in some small ways, in order simplify the library. The following settings have been removed:

CAS_LOGIN_URL and CAS_LOGOUT_URL: Version 2.0 is capable of determining these automatically.
CAS_POPULATE_USER: Subclass CASBackend instead (see above).
CAS_REDIRECT_FIELD_NAME: Django's own REDIRECT_FIELD_NAME is now used unconditionally.
CAS_USER_DETAILS_RESOLVER: template method for populating user object


Add proxy authentication
------------------------

Add the CAS proxy patch from Fredrik Jönsson Norrström

Create this as a clone to allow for any other tweaks required, and so
that it can easily pulled down for use.

- Added missing exceptions.py 
- Modified model timestamp field to not use Oracle reserved word, and ensured timestamp was added
- Added a test class that tests the full proxy authentication round trip
  as detailed at https://wiki.jasig.org/display/CAS/Proxy+CAS+Walkthrough
  NB: This class is independent of implementation so can be used to test java CAS proxies too
- Added switch to use proxyValidate CAS server call if the ticket starts with PT instead of ST

Gotchas
-------

SSL

You must ensure that the proxying server not only has SSL but that SSL has the full
chain of valid certificates. This can be checked via

openssl s_client -connect your.proxy.server:443 -verify 3 -pause -showcerts 

otherwise the SSO server will reject it as a proxy and just do ordinary authentication

Callback

The callback url for some SSO server implementations may need to be at the root
in this case you will need to add the following to your sites home page view in django
rather than handle proxy validation via a separate entry in URLs 

if request.GET.get('pgtIou',''):
    from django_cas.views import proxy_callback
    return proxy_callback(request)

