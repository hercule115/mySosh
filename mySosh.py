#!/usr/bin/env python

# Tool to get contracts information from sosh.fr

# Import or build our configuration. Must be FIRST
try:
    import config	# Shared global config variables (DEBUG,...)
except:
    #print('config.py does not exist. Generating...')
    import initConfig	# Check / Update / Create config.py module
    initConfig.initConfiguration()
    
# Import generated module
try:
    import config
except:
    print('config.py initialization has failed. Exiting')
    sys.exit(1)
    
import argparse
import builtins as __builtin__
from datetime import datetime
import inspect
import json
import logging
import os
import sys
import time

import myGlobals as mg
from common.utils import myprint, module_path, get_linenumber, color

import authinfo		# Encode/Decode credentials
import mySoshContracts as msc
        
# Arguments parser
def parse_argv():
    desc = 'Get contract information/usage from Sosh server'

    parser = argparse.ArgumentParser(description=desc)
    parser.add_argument("-s", "--server",
                        action="store_true",                        
                        dest="server",
                        default=False,
                        help="run in server mode (as a Web Service)")
    parser.add_argument("-d", "--debug",
                        action="count",
                        dest="debug",
                        default=0,
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
                        metavar='LOGFILE',
                        help="write debug messages to FILE (default to <hostname>-debug.txt)")
    parser.add_argument("-C", "--cache",
                        action="store_true",
                        dest="useCache",
                        default=True,
                        help="Use local cache if available")
    parser.add_argument('-D', '--delay',
                        dest='updateDelay',
                        default=300,
                        type=int,
                        action='store',
                        nargs='?',
                        metavar='DELAY',
                        help="update interval in seconds (Server mode only)")

    # Resources arguments
    parser.add_argument("-c", "--calls",
                        action="store_true", dest="calls", default=False,
                        help="provides information about voice calls")
    parser.add_argument("-e", "--extrabalance",
                        action="store_true", dest="extraBalance", default=False,
                        help="provides information about extra balance")
    parser.add_argument("-i", "--internet",
                        action="store_true", dest="internet", default=True,
                        help="provide information about Internet usage")

    # Credentials arguments    
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


####
def main():

    args = parse_argv()

    if args.version:
        print('%s: version %s' % (sys.argv[0], mg.VERSION))
        sys.exit(0)

    config.SERVER    = args.server
    config.VERBOSE   = args.verbose
    config.USE_CACHE = args.useCache
    config.INTERNET  = args.internet
    config.CALLS     = args.calls
    config.EXTRA_BALANCE = args.extraBalance
    config.DEBUG     = args.debug
    
    if config.DEBUG:
        myprint(1, 'Running in DEBUG mode (level=%d)' % config.DEBUG)
        myprint(1,
                'config.SERVER =', config.SERVER,
                'config.VERBOSE =', config.VERBOSE,
                'config.USE_CACHE =', config.USE_CACHE,
                'config.INTERNET =', config.INTERNET,
                'config.CALLS =', config.CALLS,
                'config.EXTRA_BALANCE =', config.EXTRA_BALANCE)
        
    if args.logFile == None:
        #print('Using stdout')
        pass
    else:
        if args.logFile == '':
            config.LOGFILE = "sosh.fr-debug.txt"
        else:
            config.LOGFILE = args.logFile
        mg.configFilePath = os.path.join(mg.moduleDirPath, config.LOGFILE)
        print('Using log file: %s' % mg.configFilePath)
        try:
            sys.stdout = open(mg.configFilePath, "w")
            sys.stderr = sys.stdout            
        except:
            print('Cannot create log file')

    if args.server:
        if args.updateDelay:
            config.UPDATEDELAY = args.updateDelay
        else:
            config.UPDATEDELAY = 300 # seconds

    if config.SERVER:
        import mySoshApiServer as msas
        if config.DEBUG:
            mg.logger.info('mySoshApiServer imported (line #%d)' % get_linenumber())

        myprint(0, 'Running in Server mode. Update interval: %d seconds (%s)' % (config.UPDATEDELAY, time.strftime('%H:%M:%S', time.gmtime(config.UPDATEDELAY))))
        res = msas.apiServerMain()	# Never returns
        myprint(1, 'mySosh API Server exited with code %d' % res)
        sys.exit(res)


    #
    # Standalone mode
    #
    if not args.contract:
        contract = 'all'
    else:
        if 'init' in args.contract:
            initConfiguration()
            print('Config initialized. Re-run the command using Sosh contract/phone number')
            sys.exit(0)
        else:
            contract = args.contract[0]

    if config.USE_CACHE:
        info = msc.getContractsInfo(contract)
        if config.VERBOSE:
            for k,v in info.items():
                oneContract = v
                print('%s%s%s' % (color.BOLD, k, color.END))
                print(json.dumps(oneContract, indent=4, ensure_ascii=False))
        else:
            print(json.dumps(info, ensure_ascii=False))
        sys.exit(0)

    # Read data from server
    res = msc.getContractsInfoFromSoshServer(mg.dataCachePath)    
    if res:
        myprint(0, 'Failed to create/update local data cache')
        sys.exit(res)

    t = os.path.getmtime(mg.dataCachePath)
    dt = datetime.fromtimestamp(t).strftime('%Y/%m/%d %H:%M:%S')
    myprint(1, 'Cache file updated. Last modification time: %s (%d)' % (dt,t))

    mg.prevModTime = t
    
    # Display information
    info = msc.getContractsInfo(contract)
    
    if config.VERBOSE:
        print(json.dumps(info, indent=4, ensure_ascii=False))
    else:
        print(json.dumps(info, ensure_ascii=False))
        
    if args.logFile and args.logFile != '':
        sys.stdout.close()
        sys.stderr.close()
        
# Entry point    
if __name__ == "__main__":

    dt_now = datetime.now().strftime("%d/%m/%Y %H:%M:%S")

    logging.basicConfig(filename='mySosh-ws.log', level=logging.INFO)
    mg.logger = logging.getLogger(__name__)
    mg.logger.info('Running at %s. Args: %s' % (dt_now, ' '.join(sys.argv)))
    
    # Absolute pathname of directory containing this module
    mg.moduleDirPath = os.path.dirname(module_path(main))

    username, password = authinfo.decodeKey(config.SOSH_AUTH.encode('utf-8'))
    
    # Absolute pathname of data cache file
    mg.dataCachePath = os.path.join(mg.moduleDirPath, '.%s%s' % (username, mg.DATA_CACHE_FILE))
    
    # Let's go
    main()
