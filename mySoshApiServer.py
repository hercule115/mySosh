#!flask/bin/python

from datetime import datetime
from dateutil.relativedelta import relativedelta
from flask import Flask, jsonify, abort, make_response
from flask_restful import Api, Resource #, reqparse, fields, marshal
import inspect
import json
import logging
from multiprocessing import Process, Value
import os
import sys
import time

import config
from common.utils import myprint
import myGlobals as mg
import mySoshContractsInfo as msci

from resources.internet import InternetAPI, InternetListAPI
from resources.extraBalance import ExtraBalanceAPI, ExtraBalanceListAPI
from resources.calls import CallsAPI, CallsListAPI

apiResources = {
    "internet" : [
        (InternetListAPI, '/mysosh/api/v1.0/internet',             'internets'),
        (InternetAPI,     '/mysosh/api/v1.0/internet/<string:id>', 'internet')
        ],
    "extrabalance" : [
        (ExtraBalanceListAPI, '/mysosh/api/v1.0/extrabalance',             'extrabalances'),
        (ExtraBalanceAPI,     '/mysosh/api/v1.0/extrabalance/<string:id>', 'extrabalance')
        ],
    "calls" : [
        (CallsListAPI, '/mysosh/api/v1.0/calls',             'calls'),
        (CallsAPI,     '/mysosh/api/v1.0/calls/<string:id>', 'call')
        ],
}

def foreverLoop(loop_on, dataCachePath, debug, updateDelay):
    config.DEBUG = debug

    class color:
        BOLD      = '\033[1m'
        UNDERLINE = '\033[4m'
        END       = '\033[0m'

    # Re-define myprint() as child process don't share globals :(
    def myprint(level, *args, **kwargs):
        import builtins as __builtin__
        
        if level <= config.DEBUG:
            __builtin__.print('%s%s()%s:' % (color.BOLD, inspect.stack()[1][3], color.END), *args, **kwargs)

    myprint(1,'Started. Updating cache file every %d seconds.' % updateDelay)
    myprint(1,'Cache file: %s' % dataCachePath)
    
    while True:
        if loop_on.value == True:
            time.sleep(updateDelay)
            myprint(0, 'Reloading cache file from server...')
            res = msci.getContractsInfoFromSoshServer(dataCachePath)
            myprint(1, 'Data collected from server')            
            if res:
                myprint(0, 'Failed to create/update local data cache')
                continue
            # Reload local cache
            mg.contractsInfo = msci.loadDataFromCache(dataCachePath)
            t = os.path.getmtime(dataCachePath)
            dt = datetime.fromtimestamp(t).strftime('%Y/%m/%d %H:%M:%S')
            myprint(0, 'Cache file reloaded. Last modification time: %s' % dt)


def apiServerMain():
    myprint(1, 'Launching Server')
    
    app = Flask(__name__, static_url_path="")
    api = Api(app)

    # Add api resources
    for resourceName, resourceParamList in apiResources.items():
        for resource in resourceParamList:
            resApi = resource[0]
            resUrl = resource[1]
            resEndpoint = resource[2]
            myprint(1, 'Adding Resource:', resourceName, resApi, resUrl, resEndpoint)
            api.add_resource(resApi, resUrl, endpoint=resEndpoint)
            
    # api.add_resource(InternetListAPI, '/mysosh/api/v1.0/internet', endpoint='internets')
    # api.add_resource(InternetAPI,     '/mysosh/api/v1.0/internet/<string:id>', endpoint='internet')

    # api.add_resource(ExtraBalanceListAPI, '/mysosh/api/v1.0/extrabalance', endpoint='extrabalances')
    # api.add_resource(ExtraBalanceAPI,     '/mysosh/api/v1.0/extrabalance/<string:id>', endpoint='extrabalance')

    # api.add_resource(CallsListAPI, '/mysosh/api/v1.0/calls', endpoint='calls')
    # api.add_resource(CallsAPI,     '/mysosh/api/v1.0/calls/<string:id>', endpoint='call')
    
    # Load data from local cache
    myprint(1, 'Loading data from cache file: %s' % mg.dataCachePath)
    mg.contractsInfo = msci.loadDataFromCache(mg.dataCachePath)
    if mg.contractsInfo == None:
        myprint(1, 'No local cache available, Connecting to server')
        res = msci.getContractsInfoFromSoshServer(mg.dataCachePath)
        if res:
            myprint(0, 'Failed to create local data cache')
            return(res)

        # Reload local cache
        mg.contractsInfo = msci.loadDataFromCache(mg.dataCachePath)

    t = os.path.getmtime(mg.dataCachePath)
    dt = datetime.fromtimestamp(t).strftime('%Y/%m/%d %H:%M:%S')
    myprint(1, 'Cache file loaded. Last modification time: %s' % dt)
        
    recording_on = Value('b', True)
    p = Process(target=foreverLoop, args=(recording_on,
                                          mg.dataCachePath,
                                          config.DEBUG,
                                          config.UPDATEDELAY))
    p.start()  
    app.run(debug=True, use_reloader=False) ##, host="0.0.0.0", port=6420)
    p.join()

    return(0)
