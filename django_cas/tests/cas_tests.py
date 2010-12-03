# Shell python script to test a live SSO set up - Ed Crewe 26 Nov 2010
# It can be really fiddly testing out SSO proxy auth via typing in URLs etc
# see Dave Spencer's guide at https://wiki.jasig.org/display/CAS/Proxy+CAS+Walkthrough 
# This does script does it for you against the deployed servers

# Run via python 2.4 or above ...
# python cas_tests.py [username]  
# You will need to edit the constants below to match your setup ...

import unittest
import sys
import commands
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
    CAS_SERVER_URL = 'https://my.sso.server/'
    APP_URL = 'http://my.client.application/'
    APP_RESTRICTED = 'restricted'
    PROXY_URL = 'https://my.proxy.application/'
    # Depending on your cas login form you may need to adjust these field name keys
    TOKEN = 'token'                    # CSRF token field name
    CAS_SUCCESS = 'Login successful'   # CAS server successful login flag (find string in html page)
    AUTH = {'username' : '',           # user field name
            'password' : '',           # password field name
            'submit' : 'Login'         # login submit button
           }
    SCRIPT = 'manage.py shell --plain < get_pgt.py' # A script to extract the PGT from your proxying server

class TestCAS(unittest.TestCase):
    """ A class for testing a CAS setup both for standard and proxy authentication """

    opener = None
    auth = {}
    urls = {}

    def setUp(self):
        cj = cookielib.CookieJar()
        opener = urllib2.build_opener(urllib2.HTTPCookieProcessor(cj))
        urllib2.install_opener(opener)
        self.opener = opener
        self.get_auth()
        self.set_url('cas', CAS_SERVER_URL)
        self.set_url('app', APP_URL)
        self.set_url('proxy', PROXY_URL)        

    def set_url(self, name, url):
        """ Make sure valid url with query string appended """
        for end in ['/','.html','.htm']:
            if url.endswith(end):
                self.urls[name] = url              
                return
        self.urls[name] = '%s/' % url  

    def test_cas(self):
        """ Test ordinary and proxy CAS login
            NB cant put these into separate tests since tickets
            are required to be passed between tests
        """
        print 'Testing with following URLs'
        print '---------------------------'        
        print 'CAS server = %s' % self.urls['cas']
        print 'Application server = %s' % self.urls['app']
        print 'Proxy CAS server = %s' % self.urls['proxy']        
        print ''
        print 'Test ordinary CAS login'
        print '-----------------------'
        self.ticket = self.login()
        self.get_restricted()

        print ''
        print 'Test proxy CAS login'
        print '--------------------'

        iou = self.proxy1_iou()
        if iou.startswith('PGT'):
            print 'PASS: Got IOU - %s for %s' % (iou, self.urls['proxy'])
        else:
            print iou

        pgt = self.proxy2_pgt(iou)
        if pgt.startswith('PGT'):
            print 'PASS: Got PGT - %s' % pgt
        else:
            print pgt

        pt = self.proxy3_pt(pgt)
        if pt.startswith('PT'):
            print 'PASS: Got PT - %s' % pt
        else:
            print pt


        proxy = self.proxy4_login(pt)
        if proxy:
            print 'PASS: Logged in successfully to %s via %s' % (self.urls['app'], proxy) 
        else:
            print 'FAIL: The proxy login to %s via %s has failed' % (self.urls['app'], self.urls['proxy']) 

        
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
        try:
            r = self.opener.open(url)
        except:
            return 'FAIL: URL not found %s' % url
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
        return dom.childNodes[0].nodeValue.strip()

    def find_in_page(self, page, starts, stop):
        """ Replace this with find_in_dom ?
            Although without knowing the CAS login page this
            is probably more generic.
            Starts is a list to allow a series of marker points
            in case a single start point marker is not unique
        """
        pagepart = page
        start = 0
        for part in starts:
            point = pagepart.find(part)
            if point>-1:
                start += point
            else:
                return "FAIL: Couldnt find '%s' in page" % part
            pagepart = pagepart[start:]
        start = start + len(part) 
        end = page[start:].find(stop)
        if end == -1:
            end = len(page[start:])
        end = start + end
        found = page[start:end]
        return found.strip()

    def login(self):
        """ Login to CAS server """
        url = '%slogin?service=%s' % (self.urls['cas'], self.urls['app'])    
        ticket = ''
        token = self.get_token(url)
        if token:
            if token.startswith('FAIL'):
                print token
                return ticket
            else:
                self.auth[TOKEN] = token
        else:
            print 'FAIL: CSRF Token could not be found on page'
            return ticket
        self.auth['service'] = self.urls['app']
        data = urllib.urlencode(self.auth)
        sso_resp = self.opener.open(url, data)
        sso_page = sso_resp.read()
        found = sso_page.find(CAS_SUCCESS) > -1
        sso_resp.close()    
        if found:
            ticket = self.get_ticket(sso_page, self.urls['app'])
            print 'PASS: CAS logged in to %s' % url 
        else:
            print 'FAIL: Couldnt login to %s' % url 
        return ticket

    def get_restricted(self):
        """ Access a restricted URL and see if its accessible """
        url = self.urls['app'] + APP_RESTRICTED
        app_resp = self.opener.open(url)
        ok = app_resp.code == 200
        app_resp.close()
        if ok:
            print 'PASS: logged in to restricted app at %s' % url
        else:
            print 'FAIL: couldnt log in to restricted app at %s' % url
        return

    def proxy1_iou(self):
        """ Use login ticket to get proxy iou
            NB: SSO server installation may require self.urls['proxy']/?pgtIou be called at the root
        """
        url_args = (self.urls['cas'], self.ticket, self.urls['app'], self.urls['proxy'])
        url = '%sserviceValidate?ticket=%s&service=%s&pgtUrl=%s' % url_args
        try:
            iou = self.opener.open(url)
        except:
            return 'FAIL: service validate url=%s not found' % url
        page = iou.read()
        if page.find('cas:authenticationSuccess') > -1:
            iou_ticket = self.find_in_dom(page,['cas:serviceResponse',
                                                'cas:authenticationSuccess',
                                                'cas:proxyGrantingTicket'])
            if iou_ticket:
                return iou_ticket
            else:
                if page:
                    return "FAIL: NO PGIOU\n\n%s" % page
                else:
                    return 'FAIL: PGIOU Empty response from %s' % url
        else:
            return 'FAIL: PGIOU Response failed authentication'
        return None

    def proxy2_pgt(self, iou):
        """ Dig out the proxy granting ticket using shell script so this test class
            is independent of CAS implementation - eg. can substitute this function
            to get proxy ticket from Java CAS instead of django-cas for example
        
            For a django-cas implementation this can be read from the ORM
            by calling the django shell environment
        """
        out = commands.getoutput(SCRIPT)
        pgt = self.find_in_page(out, ['PGT',], ' ')
        return 'PGT%s' % pgt

    def proxy3_pt(self, pgt):
        """ Use granting ticket to get proxy """
        url_args = (self.urls['cas'], self.urls['app'], pgt)
        url = '%sproxy?targetService=%s&pgt=%s' % url_args
        try:
            pt = self.opener.open(url)
        except:
            return 'FAIL: PTURL=%s not found' % url
        page = pt.read()
        if page.find('cas:serviceResponse') > -1:
            pt_ticket = self.find_in_dom(page,['cas:proxySuccess',
                                               'cas:proxyTicket'])
            return pt_ticket
        return None


    def proxy4_login(self, pt):
        """ Use proxy ticket to login """
        url_args = (self.urls['cas'], self.urls['app'], pt)
        url = '%sproxyValidate?service=%s&ticket=%s' % url_args
        try:
            login = self.opener.open(url)
        except:
            return 'FAIL: PTURL=%s not found' % url
        page = login.read()
        if page.find('cas:authenticationSuccess') > -1:
            proxy = self.find_in_dom(page,['cas:proxies',
                                               'cas:proxy'])
            return proxy
        return None

if __name__ == '__main__':
    unittest.main()
