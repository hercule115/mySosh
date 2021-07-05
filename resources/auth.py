#from flask_httpauth import HTTPBasicAuth

import config
import myGlobals as mg
from common.utils import myprint, masked

#auth = HTTPBasicAuth()

@auth.get_password
def get_password(username):
    myprint(1, 'Checking username %s' % username)
    
    u, p = authinfo.decodeKey(config.SOSH_AUTH.encode('utf-8'))
    myprint(0,u,p)

    try:
        a = getattr(config, 'SOSH_USERNAME')
    except:
        myprint(0, 'SOSH_USERNAME is not defined')
        return None

    if username != config.SOSH_USERNAME:
        myprint(0, 'Invalid username %s' % username)
        return None
        
    try:
        a = getattr(config, 'SOSH_PASSWORD')
    except:
        myprint(0, 'SOSH_PASSWORD is not defined')
        return None

    if config.VERBOSE:
        myprint(0, '%-15s: %s' % ('SOSH Username', config.SOSH_USERNAME))
        myprint(0, '%-15s: %s' % ('SOSH Password', masked(config.SOSH_PASSWORD, 3)))

    if config.DEBUG:
        myprint(1, 'Credentials are valid')
    return config.SOSH_PASSWORD

@auth.error_handler
def unauthorized():
    # return 403 instead of 401 to prevent browsers from displaying the default
    # auth dialog
    return make_response(jsonify({'message': 'Unauthorized access'}), 403)
