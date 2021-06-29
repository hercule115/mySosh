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

class InternetListAPI(Resource):
    decorators = [auth.login_required]

    def __init__(self):
    #     self.reqparse = reqparse.RequestParser()
    #     self.reqparse.add_argument('title', type=str, required=True,
    #                                help='No task title provided',
    #                                location='json')
    #     self.reqparse.add_argument('description', type=str, default="",
    #                                location='json')
    #     super(InternetListAPI, self).__init__()
        config.INTERNET = True
        config.EXTRA_BALANCE = False
        config.CALLS = False

    def get(self):
        internet = msci.getContractsInfo(mg.contractsInfo, 'all')
        myprint(1, json.dumps(internet, ensure_ascii=False))        
        return (internet)

    def post(self):
        pass

class InternetAPI(Resource):
    decorators = [auth.login_required]

    def __init__(self):
    #     self.reqparse = reqparse.RequestParser()
    #     self.reqparse.add_argument('title', type=str, location='json')
    #     self.reqparse.add_argument('description', type=str, location='json')
    #     self.reqparse.add_argument('done', type=bool, location='json')
    #     super(TaskAPI, self).__init__()
        config.INTERNET = True
        config.EXTRA_BALANCE = False
        config.CALLS = False

    def get(self, id):
        internet = msci.getContractsInfo(mg.contractsInfo, id)
        myprint(1, json.dumps(internet, ensure_ascii=False))
        return (internet)

    def put(self, id):
        pass

    def delete(self, id):
        pass
