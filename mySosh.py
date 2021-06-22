#!/usr/bin/env python

# Tool to get contracts information from sosh.fr

import builtins as __builtin__
import inspect
import os
#import math
#import socket
import sys
import requests
#import random
import time
#import getpass
import argparse
from datetime import datetime
from dateutil.relativedelta import relativedelta
from bs4 import BeautifulSoup
#import hashlib
import unicodedata
import json

import authinfo		# Encode/Decode credentials

try:
    import config	# Shared global config variables (DEBUG,...)
except:
    print('config.py does not exist. Importing generator')
    import initConfig	# Check / Update / Create config.py module

VERSION = '2.3'

DATA_CACHE_FILE = '.contracts.json'

# Dictionary containing the HTTP requests to send to the server
SOSH_HTTP_REQUESTS = {
    "initialPage" : {
        "info" : "Conect to www.sosh.fr and get index page to retrieve idzone JS URL",
        "rqst" : {
            "type" : 'GET',
            "url"  : 'https://www.sosh.fr',
            "headers" : {
                "Host"   : 'www.sosh.fr',
                "Cookie" : 'idz_usr_seg=3|false; LPVID=RkZmE1MzdjZGIyNzFmNzM5',
            },
        },
        "resp" : {
            "code" : 200,
            #"dumpResponse" : 'www.sosh.fr.html',
            "updateCookies" : False,                
        },
        "returnText" : True,
    },

    "login" : {
        "info" : 'Initiate login process, update some cookies',
        "rqst" : {
            "type" : 'GET',
            "url"  : 'https://login.orange.fr/?service=sosh&return_url=https%3A%2F%2Fwww.sosh.fr%2F',
            "headers" : {
                "Accept" : 'text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8,application/signed-exchange;v=b3;q=0.9',
                "Host"   : 'login.orange.fr',
                "Referer": 'https://www.sosh.fr/',
                "Cookie" : ['izclientid', 'idzone'],
            },
        },
        "resp" : {
            "code" : 200,
            "updateCookies" : True,
        },
        "returnText" : False,
    },

    "username" : {
        "info" : 'Continue with connection. Send username to server',
        "rqst" : {
            "type" : 'POST',
            "url"  : 'https://login.orange.fr/api/login',
            "payload" : '{"login":"put-username-here","params":{"service":"sosh","return_url":"https://www.sosh.fr/"}}',
            "extraCookie" : 'promoteMC=1',
            "headers" : {
                "Accept"         : 'application/json, text/plain, */*',
                "Host"           : 'login.orange.fr',
                "Origin"         : 'https://login.orange.fr',
                "Referer"        : 'https://login.orange.fr/',
                "Content-Type"   : 'application/json;charset=UTF-8',
                "Content-Length" : 'put-payload-length-here',
                "Cookie"         : ['xauth', 'trust', 'idzone', 'izclientid', 'datadome'],
            },
        },
        "resp" : {
            "code" : 200,
            "updateCookies" : True,
        },
        "returnText" : False,
    },

    "password" : {
        "info" : 'Continue with connection. Send password to server',        
        "rqst" : {
            "type" : 'POST',
            "url"  : 'https://login.orange.fr/api/password',
            "payload" : '{"password":"put-password-here","remember":true}',
            "extraCookie" : 'promoteMC=1',
            "headers" : {
                "Accept"         : 'application/json, text/plain, */*',
                "Host"           : 'login.orange.fr',
                "Origin"         : 'https://login.orange.fr',
                "Referer"        : 'https://login.orange.fr/',
                "Content-Type"   : 'application/json;charset=UTF-8',
                "Content-Length" : 'put-payload-length-here',
                "Cookie"         : ['xauth', 'trust', 'idzone', 'izclientid', 'datadome'],
            },
        },
        "resp" : {
            "code" : 200,
            "updateCookies" : True,
        },
        "returnText" : False,
    },

    "updateIdZone1" : {
        "info" : 'Reload index page to update idzone.js URL',
        "rqst" : {
            "type" : 'GET',
            "url"  : 'https://www.sosh.fr',
            "headers" : {
                "Accept" : 'text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8,application/signed-exchange;v=b3;q=0.9',
                "Host"   : 'www.sosh.fr',
                "Referer": 'https://login.orange.fr/',
            },
        },
        "resp" : {
            "code" : 200,
            #"dumpResponse" : 'www.sosh.fr.html',
            "updateCookies" : False,
        },
        "returnText" : True,
    },

    "proposal0" : {
        "info" : 'Use sso.orange.fr to get contracts info',
        "rqst" : {
            "type" : 'OPTIONS',
            "url"  : 'https://sso.orange.fr/pushms/advise/mct/1.1/proposal?targets=NEC[contract:50,transverse:50,contract_c:50,transverse_c:50]&canal=06ososh&data[canalPhysique]=web',
            "headers" : {
                "Host"   : 'sso.orange.fr',
                "Origin" : 'www.sosh.fr',
                "Referer": 'https://www.sosh.fr/',
                "Access-Control-Request-Method" : 'GET',
                "Access-Control-Request-Headers": 'x-capping',
                "Sec-Fetch-Mode" : 'cors',
                "Sec-Fetch-Site" : 'cross-site',
                "Sec-Fetch-Dest" : 'empty',
            },
        },
        "resp" : {
            "code" : 200,
            "updateCookies" : True,
        },
        "returnText" : False,
    },
        
    "proposal1" : {
        "info" : 'Get information about contracts',
        "rqst" : {
            "type" : 'GET',
            "url"  : 'https://sso.orange.fr/pushms/advise/mct/1.1/proposal?targets=NEC[contract:50,transverse:50,contract_c:50,transverse_c:50]&canal=06ososh&data[canalPhysique]=web',
            "headers" : {
                "Accept" : 'application/json',
                "Host"   : 'sso.orange.fr',
                "Origin" : 'www.sosh.fr',
                "Referer": 'https://www.sosh.fr/',
                "X-Capping" : '{"display": {"NEC": {"contract": {"*":1,"DEFAULT":0,"ZZZ":0},"transverse":{"*":1,"DEFAULT":0,"ZZZ":0}}}}',
                "Sec-Fetch-Mode" : 'cors',
                "Sec-Fetch-Site" : 'cross-site',
                "Sec-Fetch-Dest" : 'empty',
                "Cookie" : ['idzone', 'izclientid', 'wassup'],
            },
        },
        "resp" : {
            "code" : 200,
            "updateCookies" : True,
        },
        "returnText" : False,
    },

    "updateIdZone2" : {
        "info" : 'Reload index page to update idzone.js URL',
        "rqst" : {
            "type" : 'GET',
            "url"  : 'https://www.sosh.fr/client',
            "headers" : {
                "Accept" : 'text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8,application/signed-exchange;v=b3;q=0.9',
                "Host"   : 'www.sosh.fr',
                "Referer": 'https://www.sosh.fr/',
                "Sec-Fetch-Mode" : 'navigate',
                "Sec-Fetch-Site" : 'same-origin',
                "Sec-Fetch-Dest" : 'document',
            },
        },
        "resp" : {
            "code" : 200,
            #"dumpResponse" : 'www.sosh.fr.html',
            "updateCookies" : False,
        },
        "returnText" : True,
    },
            
    "telcoSecurity0" : {
        "info" : 'Get Telco/Security information (to update cookies)',
        "rqst" : {
            "type" : 'OPTIONS',
            "url"  : 'https://sso-f.orange.fr/omoi_erb/portfoliomanager/contracts/users/current?filter=telco,security',
            "headers" : {
                "Host"   : 'sso-f.orange.fr',
                "Origin" : 'https://www.sosh.fr',
                "Referer": 'https://www.sosh.fr/',
                "Access-Control-Request-Method" : 'GET',
                "Access-Control-Request-Headers": 'erable-service-id,x-orange-caller-id,x-orange-origin-id',
                "Sec-Fetch-Mode" : 'cors',
                "Sec-Fetch-Site" : 'cross-site',
                "Sec-Fetch-Dest" : 'empty',
            },
        },
        "resp" : {
            "code" : 204,
            "updateCookies" : True,
        },
        "returnText" : False,
    },

    "telcoSecurity1" : {
        "info" : 'Get Telco/Security information (to update cookies)',
        "rqst" : {
            "type" : 'GET',
            "url"  : 'https://sso-f.orange.fr/omoi_erb/portfoliomanager/contracts/users/current?filter=telco,security',
            "headers" : {
                "Accept" : 'application/json;version=1',
                "Host"   : 'sso-f.orange.fr',
                "Origin" : 'https://www.sosh.fr',
                "Referer": 'https://www.sosh.fr/',
                "X-Orange-Caller-Id" : 'WSH',
                "X-Orange-Origin-Id" : 'WSH',
                "Sec-Fetch-Mode" : 'cors',
                "Sec-Fetch-Site" : 'cross-site',
                "Sec-Fetch-Dest" : 'empty',
                "Cookie" : ['idzone', 'izclientid', 'wassup', 'TS01ebed15'],
            },
        },
        "resp" : {
            "code" : 200,
            "updateCookies" : True,
        },
        "returnText" : False,
    },
            
    "contracts0" : {
        "info" : 'Finally, get contracts information from server',
        "rqst" : {
            "type" : 'OPTIONS',
            "url"  : 'https://sso-f.orange.fr/omoi_erb/suiviconso/v1.0/suiviconso/users/current/contracts/',
            "headers" : {
                "Host"   : 'sso-f.orange.fr',
                "Origin" : 'https://www.sosh.fr',
                "Referer": 'https://www.sosh.fr/',
                "Access-Control-Request-Method" : 'GET',
                "Access-Control-Request-Headers": 'content-type,erable-service-id,x-orange-caller-id,x-orange-origin-id',
                "Sec-Fetch-Mode" : 'cors',
                "Sec-Fetch-Site" : 'cross-site',
                "Sec-Fetch-Dest" : 'empty',
            },
        },
        "resp" : {
            "code" : 204,
            "updateCookies" : True,
        },
        "returnText" : False,
    },

    "contracts1" : {
        "info" : 'Finally, get contracts information from server',
        "rqst" : {
            "type" : 'GET',
            "url"  : 'https://sso-f.orange.fr/omoi_erb/suiviconso/v1.0/suiviconso/users/current/contracts/',
            "headers" : {
                "Accept" : '*/*',
                "Host"   : 'sso-f.orange.fr',
                "Origin" : 'https://www.sosh.fr',
                "Referer": 'https://www.sosh.fr/',
                "Content-Type": 'application/json',
                "X-Orange-Caller-Id": 'WSH',
                "X-Orange-Origin-Id": 'WSH',
                "Sec-Fetch-Mode" : 'cors',
                "Sec-Fetch-Site" : 'cross-site',
                "Sec-Fetch-Dest" : 'empty',
                "erable-service-id": 'hpsosh',
                "Cookie" : ['idzone', 'izclientid', 'wassup', 'TS01ebed15'],
            },
        },
        "resp" : {
            "code" : 200,
            "updateCookies" : False,
        },
        "returnText" : True,
    },

    "_idzone" : {
        "info" : 'Load idzone.js Java script to update some cookies',
        "rqst" : {
            "type" : 'GET',
            "url"  : 'put-script-url-here',	# updated dynamically
            "headers" : {
                "Accept" : '*/*',
                "Host"   : 'iz4.orange.fr',
                "Referer": 'https://www.sosh.fr/',
                "Sec-Fetch-Mode" : 'no-cors',
                "Sec-Fetch-Site" : 'cross-site',
                "Sec-Fetch-Dest" : 'script',
                "Cookie" : None,	# updated dynamically
            },
        },
        "resp" : {
            "code" : 200,
            "updateCookies" : True,
        },
        "returnText" : False,
    },
}
    
####
class color:
    PURPLE    = '\033[95m'
    CYAN      = '\033[96m'
    DARKCYAN  = '\033[36m'
    BLUE      = '\033[94m'
    GREEN     = '\033[92m'
    YELLOW    = '\033[93m'
    RED       = '\033[91m'
    BOLD      = '\033[1m'
    UNDERLINE = '\033[4m'
    END       = '\033[0m'


####
class Sosh:
    def __init__(self, userName, userPassword, session):
        self._hostName = 'www.sosh.fr'
        self._username = userName
        self._password = userPassword
        self._session  = session
        
        # Dict to save cookies from server
        self._cookies = dict()
        
    @property
    def hostname(self):
        return self._hostName

    @property
    def headers(self):
        return self._headers.headers

    def getContractsInformation(self):
        assert(self._hostName)
        assert(self._session)
        assert(self._username)
        assert(self._password)

        # Execute "initialPage" request
        respText = self._executeRequest('initialPage')

        # Get idzone.js script url from response text
        idzoneScript = self._getScriptUrl(respText, 'idzone.js')

        # Load idzone.js to update cookies
        # Patch SOSH_HTTP_REQUEST[] to update the '_idzone' request with:
        # - url (from respText)
        # - list of cookies (input)
        SOSH_HTTP_REQUESTS["_idzone"]["rqst"]["url"] = 'https:%s' % idzoneScript
        SOSH_HTTP_REQUESTS["_idzone"]["rqst"]["headers"]["Cookie"] = []

        # Execute "_idzone" request
        self._executeRequest('_idzone')
        
        # Execute "login" request
        self._executeRequest('login')

        # Execute "username" request        
        # Patch SOSH_HTTP_REQUEST[] to update the 'username' request with:
        # valid 'username' from config.SOSH_USERNAME
        # valid Content-Length
        p = SOSH_HTTP_REQUESTS["username"]["rqst"]["payload"]
        myprint(2, 'Replacing %s by %s' % ("put-username-here",self._username))
        np = p.replace("put-username-here", self._username)
        SOSH_HTTP_REQUESTS["username"]["rqst"]["payload"] = np
        
        contentLen = SOSH_HTTP_REQUESTS["username"]["rqst"]["headers"]["Content-Length"]
        ncl = contentLen.replace('put-payload-length-here', str(len(np)))
        SOSH_HTTP_REQUESTS["username"]["rqst"]["headers"]["Content-Length"] = ncl

        self._executeRequest('username')

        # Execute "password" request
        # Patch SOSH_HTTP_REQUEST[] to update the 'password' request with:
        # valid 'password' from config.SOSH_PASSWORD
        # valid Content-Length
        p = SOSH_HTTP_REQUESTS["password"]["rqst"]["payload"]
        myprint(2, 'Replacing %s by %s' % ("put-password-here",self._password))        
        np = p.replace('put-password-here', self._password)
        SOSH_HTTP_REQUESTS["password"]["rqst"]["payload"] = np
        
        contentLen = SOSH_HTTP_REQUESTS["password"]["rqst"]["headers"]["Content-Length"]
        ncl = contentLen.replace('put-payload-length-here', str(len(np)))
        SOSH_HTTP_REQUESTS["password"]["rqst"]["headers"]["Content-Length"] = ncl

        self._executeRequest('password')

        # Execute "updateIdZone1" request
        respText = self._executeRequest('updateIdZone1')

        # Get idzone.js script url from response text
        idzoneScript = self._getScriptUrl(respText, 'idzone.js')

        ### Load idzone.js (to update cookies) ###
        # Patch SOSH_HTTP_REQUEST[] to update the '_idzone' request with:
        # - url
        # - list of cookies
        SOSH_HTTP_REQUESTS["_idzone"]["rqst"]["url"] = 'https:%s' % idzoneScript
        SOSH_HTTP_REQUESTS["_idzone"]["rqst"]["headers"]["Cookie"] = ['idzone', 'izclientid', 'wassup']

        # Execute "_idzone" request
        self._executeRequest('_idzone')

        # Execute "proposal0" request
        self._executeRequest('proposal0')
        self._executeRequest('proposal1')
        
        # Execute "updateIdZone2" request (again)
        respText = self._executeRequest('updateIdZone2')

        # Get idzone.js script url from response text
        idzoneScript = self._getScriptUrl(respText, 'idzone.js')
        ### Load idzone.js (to update cookies) ###
        # Patch SOSH_HTTP_REQUEST[] to update the '_idzone' request with:
        # - url
        # - list of cookies
        SOSH_HTTP_REQUESTS["_idzone"]["rqst"]["url"] = 'https:%s' % idzoneScript
        SOSH_HTTP_REQUESTS["_idzone"]["rqst"]["headers"]["Cookie"] = ['idzone', 'izclientid', 'wassup', 'TS01ebed15']

        # Execute "_idzone" request
        self._executeRequest('_idzone')
        
        # Execute "telcoSecurity*" request. (NOT REQUIRED)
        #self._executeRequest('telcoSecurity0')
        #self._executeRequest('telcoSecurity1')

        # Execute "contracts*" request
        self._executeRequest('contracts0')
        respText = self._executeRequest('contracts1')

        # Return normalized JSON data
        return(unicodedata.normalize("NFKD", respText))


    # Logout from server
    def logout(self):
        #print('BYE BYE')
        pass

        
    def _executeRequest(self, name):
        rqst = SOSH_HTTP_REQUESTS[name]
        myprint(1, 'Executing request "%s": %s' % (name, rqst["info"]))
        myprint(2, json.dumps(rqst, indent=4))

        hdrs = Headers()

        for k,v in rqst["rqst"]["headers"].items():
            if k == "Cookie":
                if 'str' in str(type(v)):	# Cookie is a string
                    cookieAsString = v
                else:				# Cookie is a list of cookies
                    assert('list' in str(type(v)))
                    cookieAsString = self._buildCookieString(v)

                # Add extra Cookie if requested
                if "extraCookie" in rqst["rqst"]:
                    cookieAsString += rqst["rqst"]["extraCookie"]
                hdrs.setHeader('Cookie', cookieAsString)
            else:
                hdrs.setHeader(k, v)

        rqstType = rqst["rqst"]["type"]
        rqstURL  = rqst["rqst"]["url"]
        
        myprint(1,'Request type: %s, Request URL: %s' % (rqstType, rqstURL))
        myprint(2,'Request Headers:', json.dumps(hdrs.headers, indent=2))

        if rqstType == 'GET':
            r = self._session.get(rqstURL, headers=hdrs.headers)
        elif rqstType == 'POST':
            rqstPayload  = rqst["rqst"]["payload"]
            myprint(1,"payload=%s" % rqstPayload)
            r = self._session.post(rqstURL, headers=hdrs.headers, data=rqstPayload)
        else:	# OPTIONS
            assert(rqstType == 'OPTIONS')
            r = self._session.options(rqstURL, headers=hdrs.headers)

        myprint(1,'Response Code:',r.status_code)

        if r.status_code != rqst["resp"]["code"]:
            myprint(1,'Invalid Status Code: %d (expected %d). Reason: %s' % (r.status_code, rqst["resp"]["code"], r.reason))
            sys.exit(1)

        # Optional parameter "dumpResponse"
        try:
            dumpResponse = rqst["resp"]["dumpResponse"]
            dumpToFile(os.path.join(moduleDirPath, dumpResponse), r.text)
        except:
            #print('No "dumpResponse" field detected')
            pass

        # Update cookies
        if rqst["resp"]["updateCookies"]:
            self._updateCookies(r.cookies)
            
        if rqst["returnText"]:
            return r.text

        
    def _findListResources (self, tag, attribute, soup):
        l = []
        for x in soup.findAll(tag):
            try:
                l.append(x[attribute])
            except KeyError:
                pass
        return(l)


    def _getScriptUrl(self, text, scriptName):
        scriptPath = ''
        
        soup = BeautifulSoup(text, 'html.parser')
        
        scripts_src = self._findListResources('script', 'src', soup)
        scriptUrl = [s for s in scripts_src if scriptName in s][0]
        return(scriptUrl)


    # Update our cookie dict
    def _updateCookies(self, cookies):
        #print(requests.utils.dict_from_cookiejar(self._session.cookies))
        for cookie in self._session.cookies:
            #print(cookie.name, cookie.value, cookie.domain)
            if cookie.value == 'undefined' or cookie.value == '':
                myprint(2,'Skipping cookie with undefined value %s' % (cookie.name))
                continue
            
            if cookie.name in self._cookies and self._cookies[cookie.name] != cookie.value:
                myprint(1,'Updating cookie:', cookie.name)
                self._cookies[cookie.name] = cookie.value
            elif not cookie.name in self._cookies:
                myprint(1,'Adding cookie:', cookie.name)
                self._cookies[cookie.name] = cookie.value
            else:
                myprint(2,'Cookie not modified:', cookie.name)                

    # Build a string containing all cookies passed as parameter in a list 
    def _buildCookieString(self, cookieList):
        cookieAsString = ''
        for c in cookieList:
            # Check if cookie exists in our dict
            if c in self._cookies:
                cookieAsString += '%s=%s; ' % (c, self._cookies[c])
            else:
                myprint(1,'Warning: Cookie %s not found.' % (c))
        return(cookieAsString)

#### Class Headers
class Headers():
    def __init__(self):

        # Request header prototype. Updated with specific request
        self._protoHeaders = {
            'Accept': 		'*/*',
            'Accept-Encoding': 	'gzip, deflate, br',
            'Accept-Language': 	'fr-FR,fr;q=0.9,en-US;q=0.8,en;q=0.7',
            'Cache-Control': 	'no-cache',
            'Connection': 	'keep-alive',
            'Pragma': 		'no-cache',
            'User-Agent': 	'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_13_6) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/87.0.4280.67 Safari/537.36'
        }

        self._h = self._protoHeaders

    @property
    def headers(self):
        return self._h

    def setHeader(self, hdr, val):
        self._h[hdr] = val

    # Return header value if found
    def getHeader(self, hdr):
        try:
            val = self._h[hdr]
        except:
            return None
        return val
    
    def getCookie(self, cookie):
        for k,v in self._h.items():
            if k == 'Set-Cookie':
                cookies = v.split(';')
                for c in cookies:
                    try:
                        cc = c.split('=')
                    except:
                        myprint(1,'Skipping %s' % cc)
                        continue
                    if cc[0] == cookie:
                        return cc[1]
        return None
        
####        
def module_path(local_function):
    ''' returns the module path without the use of __file__.  
    Requires a function defined locally in the module.
    from http://stackoverflow.com/questions/729583/getting-file-path-of-imported-module'''
    return os.path.abspath(inspect.getsourcefile(local_function))


def myprint(level, *args, **kwargs):
    """My custom print() function."""
    # Adding new arguments to the print function signature 
    # is probably a bad idea.
    # Instead consider testing if custom argument keywords
    # are present in kwargs

    if level <= config.DEBUG:
        __builtin__.print('%s%s()%s:' % (color.BOLD, inspect.stack()[1][3], color.END), *args, **kwargs)

        
# Leave the last 'l' characters of 'text' unmasked
def masked(text, l):
    nl=-(l)
    return text[nl:].rjust(len(text), "#")

    
def dumpToFile(fname, plainText):
    try:
        myprint(1,'Creating %s' % fname)
        out = open(fname, 'w')
        out.write(plainText)
        out.close()
    except IOError as e:
        msg = "I/O error: Creating %s: %s" % (fname, "({0}): {1}".format(e.errno, e.strerror))
        myprint(1,msg)
        sys.exit(1)

        
def getCookie(cookieStr, cookie):
    if not cookie in cookieStr:
        return ''

    cookies = cookieStr.split(';')
    for c in cookies:
        if c.startswith(cookie):
            return c
    return ''


def humanBytes(size):
    power = float(2**10)     # 2**10 = 1024
    n = 0
    power_labels = {0 : 'B', 1: 'KB', 2: 'MB', 3: 'GB', 4: 'TB'}
    while size > power:
        size = float(size / power)
        n += 1
    return '%s %s' % (('%.2f' % size).rstrip('0').rstrip('.'), power_labels[n])


def loadDataFromCache():
    try:
        with open(os.path.join(moduleDirPath, DATA_CACHE_FILE), 'r') as infile:
            data = infile.read()
            res = json.loads(data)
            return res
    except Exception as error: 
        myprint(1,'Unable to open cache file')
        return None

    
def showContractsInfo(contractsInfo, phonenum):
    if phonenum == 'all':
        contract = 'all'
    else: # Normalize phone number
        if '.' in phonenum:
            contract = phonenum
        elif ' ' in phonenum:
            contract = phonenum.replace(' ', '.')
        else:
            contract = '.'.join(phonenum[i:i+2] for i in range(0, len(phonenum), 2))

    if config.DEBUG:
        myprint(1,'Looking for contract: %s' % contract)

    # Dict to contain all information for all contracts
    allContracts = dict()

    for x in contractsInfo:
        try:
            e = x["equipments"][0]
        except:
            continue
        
        oneContract = dict()

        name = e["name"]
        if name.startswith('Mobile'):
            equipment = name.split(' ')[0]
            phonenum  = '.'.join(name.split(' ')[1:])

        reinitDate = e["pageInfo"]["reinitDate"]
        try:
            titleOffer = e["pageInfo"]["titleOffer"]
            oneContract['titleOffer'] = titleOffer
        except:
            titleOffer = ''
            
        oneContract['name']       = name
        oneContract['equipement'] = equipment
        oneContract['phonenum']   = phonenum

        try:
            dt = datetime.strptime(reinitDate, '%Y-%m-%dT%H:%M:%S')
            dt += relativedelta(months=1) 	# Add 1 month
            oneContract['reinitDate'] = dt.strftime('%m/%d/%y %H:%M')
        except:
            print('ERROR Converting reinitDate')
            pass

        # Create a dictionary containing info for all families for this contract
        families = dict()

        # Loop thru all families
        for f in e["families"]:
            # Each family is a dict.
            oneFamily = dict()

            # Collect various information
            oneFamily['familyCode'] = f["familyCode"]
            oneFamily['familyType'] = f["familyType"]
            oneFamily['titleLong']  = f["titleLong"]
            try:
                dt = datetime.strptime( f["date"], '%Y-%m-%dT%H:%M:%S').strftime('%m/%d/%y %H:%M')
                oneFamily['date']    = dt
            except:
                pass
            try:
                oneFamily['gaugeInfo/to'] = f["bundles"][0]["gaugeInfo"]["to"]
            except:
                pass
            try:
                oneFamily['gaugeInfo/percent'] = f["bundles"][0]["gaugeInfo"]["percent"]
            except:
                pass
            try:
                oneFamily['summary/mainText'] = f["bundles"][0]["summary"]["mainText"]
            except:
                pass
            try:
                oneFamily['appels/summary/additionalCredit'] = f["bundles"][0]["summary"]["additionalCredit"]
            except:
                pass
            
            # Add this family to global families dict for this contract
            families[oneFamily['familyCode']] = oneFamily

            # Print this family
            #print(json.dumps(oneFamily, indent=4, ensure_ascii=False))
            
        # Add families dict to this contract dict
        oneContract['families'] = families

        # Print this contract
        #print(json.dumps(oneContract, indent=4, ensure_ascii=False))
            
        # Add this contract to global allContracts dict
        allContracts[phonenum] = oneContract
            
    if config.VERBOSE:
        if contract == 'all':
            print('Showing all contracts')
            
            for k,v in allContracts.items():
                oneContract = v
                print('%s%s%s' % (color.BOLD, k, color.END))
                print(json.dumps(oneContract, indent=4, ensure_ascii=False))
        else:  
            if contract in allContracts:
                if config.DEBUG:
                    print('Contract %s FOUND' % contract)
                print(json.dumps(allContracts[contract], indent=4, ensure_ascii=False))
            else:
                if config.DEBUG:
                    print('Contract %s NOT FOUND' % contract)
    else:  # Compact mode
        outputDict = dict()
        if contract == 'all':
            for oneContract in allContracts.values():
                if config.CALLS:
                    # Show information about voice calls
                    try:
                        calls = oneContract['families']['appels']
                        value = calls['appels/summary/additionalCredit']['value'] # In seconds
                        formatted_value = time.strftime('%H:%M:%S', time.gmtime(value))
                        unit  = calls['appels/summary/additionalCredit']['unit']
                        outputDict[oneContract['phonenum']] = {
                            "value" : value,
                            "formatted_value" : formatted_value,
                            "unit"  : unit,
                        }
                    except:
                        if config.DEBUG:
                            print('No Calls')
                        outputDict[oneContract['phonenum']] = {
                            "value" : 0,
                            "formatted_value"  : "?",
                            "unit"  : "?",
                        }
                    continue
                if config.EXTRA_BALANCE:
                    # Show information for extra balance
                    try:
                        extraBalance = oneContract['families']['horsForfait']
                        extra = float(extraBalance['summary/mainText'].split(' ')[0].replace(',', '.'))
                        unit  = extraBalance['summary/mainText'].split(' ')[1]        

                        outputDict[oneContract['phonenum']] = {
                            "extra" : extra,
                            "unit"  : unit,
                            "date"  : extraBalance['date']
                        }
                        #print(json.dumps(outputDict, indent=4, ensure_ascii=False))
                        #print(outputDict)
                    except:
                        if config.DEBUG:
                            print('No Extra Balance')
                        outputDict[oneContract['phonenum']] = {
                            "extra" : 0,
                            "unit"  : "?",
                            "date"  : "?"
                        }
                        #pass
                    continue

                # Show Internet Mobile information only
                internetMobileFamily = oneContract['families']['internetMobile']

                remainAsNum = float(internetMobileFamily['summary/mainText'].split(' ')[0].replace(',', '.'))
                unit = internetMobileFamily['summary/mainText'].split(' ')[1]
                toAsNum = int(internetMobileFamily['gaugeInfo/to'].split(' ')[0])
                percent = internetMobileFamily['gaugeInfo/percent']
                used = "{:.2f}".format(toAsNum - remainAsNum)
                
                outputDict[oneContract['phonenum']] = {
                    "remain"  : remainAsNum,
                    "to"      : toAsNum,
                    "unit"    : unit,
                    "percent" : percent,
                    "used"    : float(used),
                    "expire"  : oneContract['reinitDate']
                }

            # Print collected information
            #print(json.dumps(outputDict, indent=4, ensure_ascii=False))
            print(outputDict)

        # Single contract requested
        if not contract in allContracts:
            return
        
        oneContract = allContracts[contract]

        if config.CALLS:
            # Show information about voice calls
            try:
                calls = oneContract['families']['appels']
                value = calls['appels/summary/additionalCredit']['value']
                formatted_value = time.strftime('%H:%M:%S', time.gmtime(value))                
                unit  = calls['appels/summary/additionalCredit']['unit']
                outputDict = {
                    "value" : value,
                    "formatted_value" : formatted_value,                    
                    "unit"  : unit,
                }
            except:
                if config.DEBUG:
                    print('No Calls')
                    outputDict = {
                        "value" : 0,
                        "formatted_value"  : "?",
                        "unit"  : "?",
                    }
            print(json.dumps(outputDict, ensure_ascii=False))
            return

        if config.EXTRA_BALANCE:
            # Show information for extra balance
            try:
                extraBalance = oneContract['families']['horsForfait']
                extra = float(extraBalance['summary/mainText'].split(' ')[0].replace(',', '.'))
                unit  = extraBalance['summary/mainText'].split(' ')[1]        
                outputDict = {                
                    "extra" : extra,
                    "unit"  : unit,
                    "date"  : extraBalance['date']
                }
            except:
                if config.DEBUG:
                    print('No Extra Balance')
                outputDict = {
                    "extra" : 0,
                    "unit"  : "?",
                    "date"  : "?"
                }
                #pass
            print(json.dumps(outputDict, ensure_ascii=False))
            return

        internetMobileFamily = oneContract['families']['internetMobile']
        remainAsNum = float(internetMobileFamily['summary/mainText'].split(' ')[0].replace(',', '.'))
        unit        = internetMobileFamily['summary/mainText'].split(' ')[1]        
        toAsNum     = int(internetMobileFamily['gaugeInfo/to'].split(' ')[0])
        percent     = internetMobileFamily['gaugeInfo/percent']
        used        = "{:.2f}".format(toAsNum - remainAsNum)

        outputDict = {
            "remain"  : remainAsNum,
            "to"      : toAsNum,
            "unit"    : unit,
            "percent" : percent,
            "used"    : float(used),
            "expire"  : oneContract['reinitDate']
        }
        print(json.dumps(outputDict, ensure_ascii=False))

        
# Arguments parser
def parse_argv():
    desc = 'Get data consumption from Sosh server'

    parser = argparse.ArgumentParser(description=desc)
    parser.add_argument("-d", "--debug",
                        action="count", dest="debug", default=0, #action="store_true", 
                        help="print debug messages (to stdout)")
    parser.add_argument("-v", "--verbose",
                        action="store_true", dest="verbose", default=False,
                        help="provides more information")
    parser.add_argument('-f', '--file',
                        dest='logFile',
                        const='',
                        default=None,
                        action='store',
                        nargs='?',
                        metavar='FILE',
                        help="write debug messages to FILE (default to <hostname>-debug.txt)")
    parser.add_argument("-C", "--cache",
                        action="store_true",
                        dest="useCache",
                        default=False,
                        help="Use local cache if available")

    parser.add_argument("-c", "--calls",
                        action="store_true", dest="calls", default=False,
                        help="provides information about voice calls")
    parser.add_argument("-e", "--extrabalance",
                        action="store_true", dest="extraBalance", default=False,
                        help="provides information about extra balance")
    parser.add_argument("-i", "--internet",
                        action="store_true", dest="internet", default=True,
                        help="prpvide information about Internet usage")

    parser.add_argument('-u', '--user',
                        dest='userName',
                        help="Username to use for login")
    parser.add_argument('-p', '--password',
                        dest='password',
                        help="Password to use for login")
    parser.add_argument("-I", "--info",
                        action="store_true", dest="version", default=False,
                        help="print version and exit")

    parser.add_argument('contract',
                        nargs='*',
                        help='Contract (phone num) to show (Use "all" to show all contracts or "init" to initialize the configuration)')

    args = parser.parse_args()
    return args


####
def import_module_by_path(path):
    name = os.path.splitext(os.path.basename(path))[0]
    if sys.version_info[0] == 2:
        import imp
        return imp.load_source(name, path)
    elif sys.version_info[:2] <= (3, 4):
        from importlib.machinery import SourceFileLoader
        return SourceFileLoader(name, path).load_module()
    else:
        import importlib.util
        spec = importlib.util.spec_from_file_location(name, path)
        mod = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(mod)
        return mod


#
# Import Sosh module. Must be called *after* parsing arguments
#
def importModule(moduleDirPath, moduleName, name):
    modulePath = os.path.join(moduleDirPath, moduleName)
    mod = import_module_by_path(modulePath)
    globals()[name] = mod


#
# Create configuration file config.py
#
def initConfiguration():
    import initConfig	# Check / Update / Create config.py module
    
    # Create config.py with Mandatory/Optional fields
    print('Creating config.py with Mandatory/Optional fields')
    
    mandatoryFields = [('a',['SOSH_AUTH', ('s','SOSH_USERNAME'), ('p','SOSH_PASSWORD')])]
    optionalFields  = [('b','DEBUG', 'False'),
                       ('b','VERBOSE', 'False'),
                       ('s','LOGFILE')]
                       
    initConfig.initConfig(moduleDirPath, mandatoryFields, optionalFields, True)
    return 0

####
def main():

    args = parse_argv()

    if args.version:
        print('%s: version %s' % (sys.argv[0], VERSION))
        sys.exit(0)

    config.DEBUG = args.debug

    if args.useCache:
        config.USE_CACHE = True
    else:
        config.USE_CACHE = False

    if args.calls:
        config.CALLS = True
    else:
        config.CALLS = False

    if args.extraBalance:
        config.EXTRA_BALANCE = True
    else:
        config.EXTRA_BALANCE = False
        
    if args.verbose:
        config.VERBOSE = True
    else:
        config.VERBOSE = False
        
    if not args.contract:
        #print('No contract specified. Showing all contracts')
        contract = 'all'
    else:
        # if config.VERBOSE:
        #     print('Initializing configuration')
        if 'init' in args.contract:
            initConfiguration()
            print('Config initialized. Re-run the command using Sosh contract/phone number')
            sys.exit(0)
        else:
            contract = args.contract[0]

    if config.USE_CACHE:
        contractsInfo = loadDataFromCache()
        if contractsInfo:
            # Display data usage information
            showContractsInfo(contractsInfo, contract)
            sys.exit(0)
        else:
            myprint(1,'No cache available, Connecting to server')

    username, password = authinfo.decodeKey(config.SOSH_AUTH.encode('utf-8'))

    # If username / paswword have been provided on the command-line, use them
    try:
        a = getattr(config, 'SOSH_USERNAME')
    except:
        setattr(config, 'SOSH_USERNAME', username)
        
    try:
        a = getattr(config, 'SOSH_PASSWORD')
    except:
        setattr(config, 'SOSH_PASSWORD', password)

    if config.VERBOSE:
        print('%-15s: %s' % ('SOSH Username', config.SOSH_USERNAME))
        print('%-15s: %s' % ('SOSH Password', masked(config.SOSH_PASSWORD, 3)))

    with requests.session() as session:
        if args.logFile == None:
            #print('Using stdout')
            pass
        else:
            if args.logFile == '':
                config.LOGFILE = "sosh.fr-debug.txt"
            else:
                config.LOGFILE = args.logFile
            print('Using log file: %s' % config.LOGFILE)
            try:
                sys.stdout = open(os.path.join(moduleDirPath, config.LOGFILE), "w")
            except:
                print('Cannot create log file')

        # Create connection at hostName, connect with given credentials
        sosh = Sosh(config.SOSH_USERNAME, config.SOSH_PASSWORD, session)

        # Read current contracts information
        contractsInfo = sosh.getContractsInformation()

    # Update data cache
    dumpToFile(os.path.join(moduleDirPath, DATA_CACHE_FILE), contractsInfo)

    # Display data usage information
    showContractsInfo(json.loads(contractsInfo), contract)
        
    # Work done. Logout from server
    sosh.logout()

    if args.logFile and args.logFile != '':
        sys.stdout.close()
        
# Entry point    
if __name__ == "__main__":

    # Absolute pathname of directory containing this module
    moduleDirPath = os.path.dirname(module_path(main))

    # Check if config module is already imported. If not, build it
    try:
        x = globals()['config']
        haveConfig = True
    except:
        haveConfig = False

    if not haveConfig:
        initConfiguration()

    # Import generated module
    try:
        import config
    except:
        print('config.py initialization has failed. Exiting')
        sys.exit(1)
            
    # Let's go
    main()

########
#        "horsForfait": {
#            "familyCode": "horsForfait",
#            "familyType": "extra_balance",
#            "titleLong": "Hors forfait",
#            "date": "06/04/21 00:00",
#            "summary/mainText": "7,04 €"
#        },


                        # "familyCode": "appels",
                        # "familyType": "calls",
                        # "title": "Appels",
                        # "titleLong": "Appels",
                        # "date": "",
                        # "dateText": "",
                        # "bundles": [
                        #     {
                        #         "bundleCode": "LIBI",
                        #         "bundleType": "LIBI",
                        #         "summary": {
                        #             "stateText": "Illimite\u0301",
                        #             "additionalText": "Consomme\u0301 : 3 min 37 s",
                        #             "additionalCredit": {
                        #                 "value": 217,
                        #                 "unit": "TIME"
                        #             },
                        #             "displayAlertIcon": false,
                        #             "displayTopup": false,
                        #             "displayGauge": false
                        #         },
                        #         "userActivityAccess": false
                        #     }
                        # ]
