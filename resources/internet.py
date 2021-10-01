from flask import jsonify, make_response # redirect, request, url_for, current_app, flash, 
from flask_restful import Api, Resource
from flask_httpauth import HTTPBasicAuth
import json

import config
import authinfo
import mySoshContracts as msc
import myGlobals as mg
from common.utils import myprint, masked

auth = HTTPBasicAuth()

@auth.get_password
def get_password(username):
    myprint(1, 'Checking username %s' % username)
    
    u, p = authinfo.decodeKey(config.SOSH_AUTH.encode('utf-8'))

    myprint(1, '%-15s: %s' % ('SOSH Username', u))
    myprint(1, '%-15s: %s' % ('SOSH Password', masked(p, 3)))

    if u == '':
        myprint(0, 'Unable to decode config.SOSH_AUTH')
        return None

    if username != u:
        myprint(0, 'Invalid username %s' % username)
        return None

    myprint(2, 'Username is valid')
    return p

@auth.error_handler
def unauthorized():
    # return 403 instead of 401 to prevent browsers from displaying the default
    # auth dialog
    return make_response(jsonify({'message': 'Unauthorized access'}), 403)

class InternetListAPI(Resource):
    decorators = [auth.login_required]

    def __init__(self):
        config.EXTRA_BALANCE = False
        config.CALLS         = False
        config.MISCINFO      = False
        config.INTERNET      = True
        
    def get(self):
        internet = msc.getContractsInfo('all')
        myprint(1, json.dumps(internet, ensure_ascii=False))        
        return (internet)

    def post(self):
        pass

class InternetAPI(Resource):
    decorators = [auth.login_required]

    def __init__(self):
        config.EXTRA_BALANCE = False
        config.CALLS         = False
        config.MISCINFO      = False
        config.INTERNET      = True
        
    def get(self, id):
        internet = msc.getContractsInfo(id)
        myprint(1, json.dumps(internet, ensure_ascii=False))
        return (internet)

    def put(self, id):
        pass

    def delete(self, id):
        pass
