import myGlobals as mg
from common.utils import get_linenumber
from datetime import datetime
from dateutil.relativedelta import relativedelta
from flask import Flask
from flask_restful import Api, Resource
import inspect
import json
from multiprocessing import Process, Value
import os
import sys
import time

import config
from common.utils import myprint, isFileOlderThanXMinutes

import mySoshContracts as msc

from resources.internet import InternetAPI, InternetListAPI
from resources.extraBalance import ExtraBalanceAPI, ExtraBalanceListAPI
from resources.calls import CallsAPI, CallsListAPI

DATACACHE_AGING_IN_MINUTES = 20

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

    myprint(1,'Started. Updating cache file every %d seconds (%s).' % (updateDelay, time.strftime('%H:%M:%S', time.gmtime(updateDelay))))
    myprint(1,'Cache file: %s' % dataCachePath)
    
    while True:
        if loop_on.value == True:
            time.sleep(updateDelay)
            myprint(0, 'Reloading cache file from server...')
            res = msc.getContractsInfoFromSoshServer(dataCachePath)
            if res:
                myprint(0, 'Failed to create/update local data cache')
                #continue
            dt_now = datetime.now().strftime("%d/%m/%Y %H:%M:%S")
            myprint(0, 'Data collected from server at %s' % (dt_now))            

            # Reload local cache
            #myprint(0,'0 mg.contractsInfo',type(mg.contractsInfo),len(mg.contractsInfo))
            #mg.contractsInfo = ''
            #mg.contractsInfo = msc.loadDataFromCache(dataCachePath)
            #myprint(0,'2 mg.contractsInfo',type(mg.contractsInfo),len(mg.contractsInfo))
            #t = os.path.getmtime(dataCachePath)
            #dt = datetime.fromtimestamp(t).strftime('%Y/%m/%d %H:%M:%S')
            #myprint(0, 'Cache file reloaded (len=%d). Last modification time: %s' % (len(str(mg.contractsInfo)), dt))


def apiServerMain():

    dt_now = datetime.now().strftime("%d/%m/%Y %H:%M:%S")
    mg.logger.info('Launching server at %s' % dt_now)
    myprint(1, 'Launching server...')
    
    app = Flask(__name__, static_url_path="")
    api = Api(app)

    for resourceName, resourceParamList in apiResources.items():
        for resource in resourceParamList:
            resApi = resource[0]
            resUrl = resource[1]
            resEndpoint = resource[2]
            myprint(1, 'Adding Resource:', resourceName, resApi, resUrl, resEndpoint)
            api.add_resource(resApi, resUrl, endpoint=resEndpoint)
            
    # Check if local cache file exists.
    # In this case, check its modification time and reload it from Sosh server if too old.
    if os.path.isfile(mg.dataCachePath):
        if isFileOlderThanXMinutes(mg.dataCachePath, minutes=DATACACHE_AGING_IN_MINUTES):
            t = os.path.getmtime(mg.dataCachePath)
            dt = datetime.fromtimestamp(t).strftime('%Y/%m/%d %H:%M:%S')
            myprint(0, 'Cache file outdated (%s). Deleting and reloading from Sosh server' % dt)
            os.remove(mg.dataCachePath)
            
    # Load data from local cache
    myprint(0, 'Loading data from cache file: %s' % mg.dataCachePath)
    mg.contractsInfo = msc.loadDataFromCache(mg.dataCachePath)
    #myprint(0,'1 mg.contractsInfo',type(mg.contractsInfo),len(mg.contractsInfo))
    if mg.contractsInfo == None:
        myprint(0, 'No local cache available, Connecting to server')
        res = msc.getContractsInfoFromSoshServer(mg.dataCachePath)
        if res:
            myprint(0, 'Failed to create local data cache')
            return(res)

        # Reload local cache
        mg.contractsInfo = msc.loadDataFromCache(mg.dataCachePath)

    t = os.path.getmtime(mg.dataCachePath)
    dt = datetime.fromtimestamp(t).strftime('%Y/%m/%d %H:%M:%S')
    myprint(0, 'Cache file loaded (len=%d). Last modification time: %s (%d)' % (len(str(mg.contractsInfo)), dt, t))

    mg.prevModTime = t
    
    recording_on = Value('b', True)
    p = Process(target=foreverLoop, args=(recording_on,
                                          mg.dataCachePath,
                                          config.DEBUG,
                                          config.UPDATEDELAY))
    p.start()  
    app.run(debug=True, use_reloader=False, port=5000) ##, host="0.0.0.0", port=6420)
    p.join()

    return(0)
