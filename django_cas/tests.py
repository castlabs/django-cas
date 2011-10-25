from StringIO import StringIO
from unittest.case import TestCase
import urllib
from django.conf import settings

from django_cas.backends import _verify_cas2

__author__ = 'sannies'

def dummyUrlOpenNoProxyGrantingTicket(url):
    return StringIO('<cas:serviceResponse xmlns:cas="http://www.yale.edu/tp/cas"><cas:authenticationSuccess><cas:user>sannies</cas:user><cas:attributes><cas:attraStyle>Jasig</cas:attraStyle><cas:merchant>sannies</cas:merchant><cas:userServerUrl>http://localhost:8080/user-authorization-adapter/</cas:userServerUrl><cas:firstname></cas:firstname><cas:lastname></cas:lastname><cas:is_superuser>True</cas:is_superuser><cas:is_staff>True</cas:is_staff><cas:ROLES>ROLE_SUPERUSER</cas:ROLES><cas:ROLES>ROLE_STAFF</cas:ROLES><cas:ROLES>ROLE_USER</cas:ROLES><cas:ROLES>ROLE_MERCHANT</cas:ROLES><cas:playReadyLicenseAcquisitionUiUrl>http://www.drmtoday.com/</cas:playReadyLicenseAcquisitionUiUrl><cas:email>Sebastian.Annies@castlabs.com</cas:email></cas:attributes></cas:authenticationSuccess></cas:serviceResponse>')



class backendTest(TestCase):
    def test_verify_cas2(self):
        urllib.urlopen = dummyUrlOpenNoProxyGrantingTicket
        settings.CAS_PROXY_CALLBACK = None
        user = _verify_cas2('ST-jkadfhjksdhjkfh', 'http://dummy')
        self.assertEqual('sannies', user)
  