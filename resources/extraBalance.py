from flask_restful import Resource
from flask_httpauth import HTTPBasicAuth
import json

import config
import mySoshContractsInfo as msci
import myGlobals as mg
from common.utils import myprint

auth = HTTPBasicAuth()

@auth.get_password
def get_password(username):
    myprint(2, username)
    if username == 'didier':
        return 'foobar'
    return None


@auth.error_handler
def unauthorized():
    # return 403 instead of 401 to prevent browsers from displaying the default
    # auth dialog
    return make_response(jsonify({'message': 'Unauthorized access'}), 403)

class ExtraBalanceListAPI(Resource):
    decorators = [auth.login_required]

    def __init__(self):
        config.INTERNET = False
        config.EXTRA_BALANCE = True
        config.CALLS = False

    def get(self):
        extra = msci.getContractsInfo(mg.contractsInfo, 'all')
        myprint(1, json.dumps(extra, ensure_ascii=False))        
        return (extra)

    def post(self):
        pass

class ExtraBalanceAPI(Resource):
    decorators = [auth.login_required]

    def __init__(self):
        config.INTERNET = False
        config.EXTRA_BALANCE = True
        config.CALLS = False
    
    def get(self, id):
        extra = msci.getContractsInfo(mg.contractsInfo, id)
        myprint(1, json.dumps(extra, ensure_ascii=False))
        return (extra)

    def put(self, id):
        pass

    def delete(self, id):
        pass