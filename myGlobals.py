# Some glogal constants
VERSION = '3.1'
DATA_CACHE_FILE = '.contracts.json'

# Global variables
logger = None
moduleDirPath = ''
dataCachePath = ''
contractsInfo = None
prevModTime = 0
allContracts = {}

# Config parameters
mandatoryFields = [('a',['SOSH_AUTH', ('s','SOSH_USERNAME'), ('p','SOSH_PASSWORD')])]
optionalFields  = [('d','DEBUG', 0),
                   ('b','VERBOSE', 'False'),
                   ('s','LOGFILE')]
