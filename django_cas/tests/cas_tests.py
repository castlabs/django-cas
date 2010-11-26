# Shell python script to test a live SSO set up - Ed Crewe 26 Nov 2010
# It can be really fiddly testing out SSO proxy auth via typing in URLs etc
# see Dave Spencer's guide at https://wiki.jasig.org/display/CAS/Proxy+CAS+Walkthrough 
# This does script does it for you against the deployed servers

# Run via python 2.4 or above ...
# python proxy_test.py username password
# You will need to edit the constants below to match your setup ...

import sys
import urllib2
import urllib
from urlparse import urljoin
import cookielib

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

def get_auth():
    """ Get authentication by passing to this script on the command line """
    if len(sys.argv) == 3:
        AUTH['username'] = sys.argv[1]
        AUTH['password'] = sys.argv[2]         
        return AUTH
    else:
        print 'You must call the test via:'
        print 'python proxy_test.py username password'

def get_token(opener, url, token=TOKEN):
    """ Get CSRF token """
    r = opener.open(url)
    page = r.read()
    starts = ['<input type="hidden" name="%s"' % token,
              'value="']
    return find_in_page(page, starts, '"')

def get_ticket(page, app_url):
    """ Get CSRF token """
    starts = [app_url,'?ticket=']
    return find_in_page(page, starts, '"')

def find_in_page(page, starts, stop):
    """ make this less ugly and more generic with regex """
    end = page.find(starts[0])
    start = end + page[end:].find(starts[1]) + len(starts[1])
    end = start + page[start:].find(stop)
    found = page[start:end]
    return found

def login(opener, auth):
    """ Login to CAS server """
    url = '%s/login?service=%s' % (CAS_SERVER_URL, APP_URL)    
    ticket = ''
    token = get_token(opener, url)
    if token:
        auth[TOKEN] = token
    else:
        print 'FAILED CSRF Token could not be found on page'
        return ticket
    auth['service'] = APP_URL
    data = urllib.urlencode(auth)
    sso_resp = opener.open(url, data)
    sso_page = sso_resp.read()
    found = sso_page.find(CAS_SUCCESS) > -1
    sso_resp.close()    
    if found:
        ticket = get_ticket(sso_page, APP_URL)
        print 'PASS CAS logged in to %s' % url 
    else:
        print 'FAILED CAS login to %s' % url 
    return ticket

def get_restricted(opener):
    """ Access a restricted URL and see if its accessible """
    url = APP_URL + APP_RESTRICTED
    app_resp = opener.open(url)
    ok = app_resp.code == 200
    app_resp.close()
    if ok:
        print 'PASS logged in to restricted app at %s' % url
    else:
        print 'FAILED to log in to restricted app at %s' % url
    return

def get_proxy(opener, ticket):
    """ Use login ticket to get proxy """
    url_args = (CAS_SERVER_URL, ticket, APP_URL, PROXY_URL)
    iou_url = '%s/serviceValidate?ticket=%s&service=%s&pgtUrl=%s' % url_args
    iou = opener.open(iou_url)
    print iou.read()

cj = cookielib.CookieJar()
opener = urllib2.build_opener(urllib2.HTTPCookieProcessor(cj))
urllib2.install_opener(opener)
auth = get_auth()
print 'Test ordinary CAS login'
print '-----------------------'
ticket = login(opener, auth)
get_restricted(opener)
print ''
print 'Test proxy CAS login'
print '--------------------'
get_proxy(opener, ticket)
