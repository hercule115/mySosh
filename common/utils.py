import builtins as __builtin__
import inspect
import os
import sys
import time

import myGlobals as mg

try:
    import config	# Shared global config variables (DEBUG,...)
except:
    print('The file config.py does not exist. Initializing configuration')
    import initConfig	# Check / Update / Create config.py module

# Check if config module is already imported. If not, build it
try:
    x = globals()['config']
    haveConfig = True
except:
    haveConfig = False

if not haveConfig:
    initConfig.initConfiguration()

# Import generated module
try:
    import config
except:
    print('config.py initialization has failed. Exiting')
    sys.exit(1)

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
        
####
def dumpToFile(fname, plainText):
    try:
        myprint(1,'Creating/Updating %s' % fname)
        out = open(fname, 'w')
        out.write(plainText)
        out.close()
    except IOError as e:
        msg = "I/O error: Creating %s: %s" % (fname, "({0}): {1}".format(e.errno, e.strerror))
        myprint(1,msg)
        return(1)
    return(0)

####
def humanBytes(size):
    power = float(2**10)     # 2**10 = 1024
    n = 0
    power_labels = {0 : 'B', 1: 'KB', 2: 'MB', 3: 'GB', 4: 'TB'}
    while size > power:
        size = float(size / power)
        n += 1
    return '%s %s' % (('%.2f' % size).rstrip('0').rstrip('.'), power_labels[n])

####
def isFileOlderThanXMinutes(file, minutes=1): 
    fileTime = os.path.getmtime(file) 
    # Check against minutes parameter
    #return ((time.time() - fileTime) / 3600 > 24*days)
    return ((time.time() - fileTime) > (minutes *  60))

####
from inspect import currentframe

def get_linenumber():
    cf = currentframe()
    return cf.f_back.f_lineno
