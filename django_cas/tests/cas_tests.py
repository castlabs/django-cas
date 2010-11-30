# Shell python script to test a live SSO set up - Ed Crewe 26 Nov 2010
# It can be really fiddly testing out SSO proxy auth via typing in URLs etc
# see Dave Spencer's guide at https://wiki.jasig.org/display/CAS/Proxy+CAS+Walkthrough 
# This does script does it for you against the deployed servers

# Run via python 2.4 or above ...
# python cas_tests.py [username]  
# You will need to edit the constants below to match your setup ...

import unittest
import sys
import getpass
import urllib2
import urllib
from urlparse import urljoin
import cookielib
from xml.dom import minidom

# Add in a separate test_config file if you wish of the following format
try:
    from test_config import *
except:
    # Please edit these urls to match your cas server, proxy and app server urls
    CAS_SERVER_URL = 'https://my.sso.server'
    APP_URL = 'http://my.client.application'
    APP_RESTRICTED = 'restricted'
    PROXY_URL = 'https://my.proxy.application'
    # Depending on your cas login form you may need to adjust these field name keys
    TOKEN = 'token'                    # CSRF token field name
    CAS_SUCCESS = 'Login successful'   # CAS server successful login flag (find string in html page)
    AUTH = {'username' : '',           # user field name
            'password' : '',           # password field name
            'submit' : 'Login'         # login submit button
           }

class TestCAS(unittest.TestCase):
    """ A class for testing a CAS setup both for standard and proxy authentication """

    opener = None
    auth = {}

    def setUp(self):
        cj = cookielib.CookieJar()
        opener = urllib2.build_opener(urllib2.HTTPCookieProcessor(cj))
        urllib2.install_opener(opener)
        self.opener = opener
        self.get_auth()

    def test_cas(self):
        """ Test ordinary and proxy CAS login
            NB cant put these into separate tests since tickets
            are required to be passed between tests
        """
        print 'Test ordinary CAS login'
        print '-----------------------'
        self.ticket = self.login()
        self.get_restricted()
        print 'Test proxy CAS login'
        print '--------------------'
        iou = self.get_proxy_iou()
        if iou:
            print 'Got IOU:%s' % iou
        else:
            print 'Proxy CAS login failed, no IOU'
        pgt = self.get_proxy(iou)
        if pgt:
            print 'Got PGT:%s' % pgt
        else:
            print 'Proxy CAS login failed, no PGT'
        
    def get_auth(self):
        """ Get authentication by passing to this script on the command line """
        if len(sys.argv) > 1:
            self.auth['username'] = sys.argv[1]
        else:
            self.auth['username'] = getpass.getuser()
        self.auth['password'] = getpass.getpass('CAS Password for user %s:' % AUTH['username'])        
        return 

    def get_token(self, url, token=TOKEN):
        """ Get CSRF token """
        r = self.opener.open(url)
        page = r.read()
        starts = ['<input type="hidden" name="%s"' % token,
                  'value="']
        return self.find_in_page(page, starts, '"')

    def get_ticket(self, page, app_url):
        """ Get CSRF token """
        starts = [app_url,'?ticket=']
        return self.find_in_page(page, starts, '"')

    def find_in_dom(self, page, nesting=['body','form']):
        """ Use dom to get values from XML or page """
        dom = minidom.parseString(page)
        for level in nesting:
            try:
                dom = dom.getElementsByTagName(level)[0]
            except:
                break
        return dom.childNodes[0].nodeValue

    def find_in_page(self, page, starts, stop):
        """ Replace this with find_in_dom ?
            Although without knowing the CAS login page this
            is probably more generic.
        """
        end = page.find(starts[0])
        start = end + page[end:].find(starts[1]) + len(starts[1])
        end = start + page[start:].find(stop)
        found = page[start:end]
        return found

    def login(self):
        """ Login to CAS server """
        url = '%s/login?service=%s' % (CAS_SERVER_URL, APP_URL)    
        ticket = ''
        token = self.get_token(url)
        if token:
            self.auth[TOKEN] = token
        else:
            print 'FAILED CSRF Token could not be found on page'
            return ticket
        self.auth['service'] = APP_URL
        data = urllib.urlencode(self.auth)
        sso_resp = self.opener.open(url, data)
        sso_page = sso_resp.read()
        found = sso_page.find(CAS_SUCCESS) > -1
        sso_resp.close()    
        if found:
            ticket = self.get_ticket(sso_page, APP_URL)
            print 'PASS CAS logged in to %s' % url 
        else:
            print 'FAILED CAS login to %s' % url 
        return ticket

    def get_restricted(self):
        """ Access a restricted URL and see if its accessible """
        url = APP_URL + APP_RESTRICTED
        app_resp = self.opener.open(url)
        ok = app_resp.code == 200
        app_resp.close()
        if ok:
            print 'PASS logged in to restricted app at %s' % url
        else:
            print 'FAILED to log in to restricted app at %s' % url
        return

    def get_proxy_iou(self):
        """ Use login ticket to get proxy iou """
        url_args = (CAS_URL, self.ticket, APP_URL, PROXY_URL)
        url = '%s/serviceValidate?ticket=%s&service=%s&pgtUrl=%s' % url_args
        iou = self.opener.open(url)
        page = iou.read()
        if page.find('cas:authenticationSuccess') > -1:
            iou_ticket = self.find_in_dom(page,['cas:serviceResponse',
                                                'cas:authenticationSuccess',
                                                'cas:proxyGrantingTicket'])
            return iou_ticket
        return None

    def get_proxy(self, iou):
        """ Use login ticket to get proxy """
        url_args = (PROXY_URL, iou)
        url = '%s/pgtCallback?pgtIou=%s' % url_args
        return url
        pgt = self.opener.open(url)
        page = pgt.read()
        return page
        if page.find('cas:authenticationSuccess') > -1:
            pgt_ticket = self.find_in_dom(page,['cas:serviceResponse',
                                                'cas:authenticationSuccess',
                                                'cas:proxyGrantingTicket'])
            return pgt_ticket
        return None

if __name__ == '__main__':
    unittest.main()
