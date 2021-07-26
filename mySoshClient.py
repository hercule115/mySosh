from bs4 import BeautifulSoup
import json
import os
import requests
import sys
import unicodedata

from common.utils import myprint, dumpToFile
import myGlobals as mg
import authinfo
import config

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
            myprint(0,'Request %s (%s). Invalid Status Code: %d (expected %d). Reason: %s.' % (name, rqst["info"], r.status_code, rqst["resp"]["code"], r.reason))
            if rqst["returnText"]:
                return ''
            else:
                return

        # Optional parameter "dumpResponse"
        try:
            dumpResponse = rqst["resp"]["dumpResponse"]
            dumpToFile(os.path.join(mg.moduleDirPath, dumpResponse), r.text)
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
    
