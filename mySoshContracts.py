from datetime import datetime
from dateutil.relativedelta import relativedelta
import json
import os
import requests
import time

import myGlobals as mg
import authinfo
import config

import mySoshClient
from common.utils import myprint, dumpToFile, masked, color

#allContracts = dict()
#print('allContracts initialized')

####
# Reload data from cache file if needed.
# Parse data to build the allContracts dict. 
def getDataFromCache():
    # What time is it ?
    dtNow = datetime.now().strftime("%Y/%m/%d %H:%M:%S")
    
    # Check if cache file has been updated by server thread
    currModTime = os.path.getmtime(mg.dataCachePath)
    dt = datetime.fromtimestamp(currModTime).strftime('%Y/%m/%d %H:%M:%S')
    myprint(1, '%s: Cache file last modification time: %s (%d)' % (dtNow,dt,currModTime))

    if currModTime > mg.prevModTime:
        myprint(1, 'Need to reload cache data from cache file (%d/%d)' % (mg.prevModTime,currModTime))
        # Reload local cache
        rawInfo = loadDataFromCacheFile(mg.dataCachePath)
        mg.prevModTime = currModTime
        # Rebuild allContracts dictionary
        mg.allContracts = buildAllContracts(rawInfo)
    else:
        myprint(1, 'Data cache is up to date')

    myprint(1, 'allContracts #entries: %d' % (len(mg.allContracts)))
    return mg.allContracts

    
####
# Build allContracts dictionnary with relevant information from data cache file    
def buildAllContracts(rawInfo):
    myprint(1, 'Building AllContracts dictionary from raw data (# contracts=%d)' % (len(rawInfo)))

    # Dict to contain all information for all contracts
    allContracts = dict()

    for x in rawInfo:
        try:
            e = x["equipments"][0]
        except:
            continue
        
        oneContract = dict()

        name = e["name"]
        if name.startswith('Mobile'):
            equipment = name.split(' ')[0]
            phonenum  = '.'.join(name.split(' ')[1:])

        reinitDate = e["pageInfo"]["reinitDate"]
        try:
            titleOffer = e["pageInfo"]["titleOffer"]
            oneContract['titleOffer'] = titleOffer
        except:
            titleOffer = ''
            
        oneContract['name']       = name
        oneContract['equipement'] = equipment
        oneContract['phonenum']   = phonenum

        try:
            dt = datetime.strptime(reinitDate, '%Y-%m-%dT%H:%M:%S')
            dt += relativedelta(months=1) 	# Add 1 month
            oneContract['reinitDate'] = dt.strftime('%m/%d/%y %H:%M')
        except:
            myprint(1, 'Cannot convert reinitDate: %s' % reinitDate)
            pass

        # Create a dictionary containing info for all families for this contract
        families = dict()

        # Loop thru all families
        for f in e["families"]:
            # Each family is a dict.
            oneFamily = dict()

            # Collect various information
            oneFamily['familyCode'] = f["familyCode"]
            oneFamily['familyType'] = f["familyType"]
            oneFamily['titleLong']  = f["titleLong"]
            try:
                dt = datetime.strptime( f["date"], '%Y-%m-%dT%H:%M:%S').strftime('%m/%d/%y %H:%M')
                oneFamily['date'] = dt
            except:
                myprint(1, 'Contract: %s Family: %s: Failed to decode "date" field' % (phonenum,f["familyCode"]))
                pass
            try:
                oneFamily['gaugeInfo/to'] = f["bundles"][0]["gaugeInfo"]["to"]
            except:
                myprint(1, 'Contract: %s: Family: %s: Failed to decode "gaugeInfo/to" field' % (phonenum,f["familyCode"]))
                pass
            try:
                oneFamily['gaugeInfo/percent'] = f["bundles"][0]["gaugeInfo"]["percent"]
            except:
                myprint(1, 'Contract: %s: Family: %s: Failed to decode "gaugeInfo/percent" field' % (phonenum,f["familyCode"]))
                pass
            try:
                oneFamily['summary/mainText'] = f["bundles"][0]["summary"]["mainText"]
            except:
                myprint(1, 'Contract: %s: Family: %s: Failed to decode "summary/mainText" field' % (phonenum,f["familyCode"]))
                pass
            try:
                oneFamily['appels/summary/additionalCredit'] = f["bundles"][0]["summary"]["additionalCredit"]
            except:
                myprint(1, 'Contract: %s: Family: %s: Failed to decode "summary/additionalCredit" field' % (phonenum,f["familyCode"]))
                pass
            
            # Add this family to global families dict for this contract
            families[oneFamily['familyCode']] = oneFamily

            # Print this family
            #print(json.dumps(oneFamily, indent=4, ensure_ascii=False))
            
        # Add families dict to this contract dict
        oneContract['families'] = families

        # Print this contract
        #print(json.dumps(oneContract, indent=4, ensure_ascii=False))
            
        # Add this contract to global allContracts dict
        allContracts[phonenum] = oneContract
    
    return allContracts


###
# Load raw data from cache file
def loadDataFromCacheFile(dataCachePath):
    try:
        with open(dataCachePath, 'r') as infile:
            data = infile.read()
            res = json.loads(data)
            return res
    except Exception as error: 
        myprint(0, f"Unable to open data cache file {dataCachePath}")
        return None

    
####
def getContractsInfo(phonenum):
    
    if phonenum == 'all':
        contract = 'all'
    else: # Normalize phone number
        if '.' in phonenum:
            contract = phonenum
        elif ' ' in phonenum:
            contract = phonenum.replace(' ', '.')
        else:
            contract = '.'.join(phonenum[i:i+2] for i in range(0, len(phonenum), 2))

    myprint(1, 'Looking for contract: %s%s%s' % (color.BOLD, contract, color.END))

    allContracts = getDataFromCache()
    
    if config.VERBOSE:
        if contract == 'all':
            myprint(0, 'Showing all contracts')
            return(allContracts)
        elif contract in allContracts:
            if config.DEBUG:
                myprint(1, 'Contract %s FOUND' % contract)
                return(allContracts[contract])
            else:
                if config.DEBUG:
                    myprint(1, 'Contract %s NOT FOUND' % contract)
                return()
        else:
            return()

    # Compact mode

    outputDict = dict()
    myprint(1, 'Generating outputDict for "contract" %s' % (contract))

    if contract == 'all':
        for oneContract in allContracts.values():
            if config.CALLS:
                # Show information about voice calls
                try:
                    calls = oneContract['families']['appels']
                    value = calls['appels/summary/additionalCredit']['value'] # In seconds
                    formatted_value = time.strftime('%H:%M:%S', time.gmtime(value))
                    unit  = calls['appels/summary/additionalCredit']['unit']
                    outputDict[oneContract['phonenum']] = {
                        "value" : value,
                        "formatted_value" : formatted_value,
                        "unit"  : unit,
                    }
                except:
                    myprint(1, 'No Calls')
                    outputDict[oneContract['phonenum']] = {
                        "value" : 0,
                        "formatted_value"  : "?",
                        "unit"  : "?",
                    }
                continue

            if config.EXTRA_BALANCE:
                # Show information for extra balance
                try:
                    extraBalance = oneContract['families']['horsForfait']
                    extra = float(extraBalance['summary/mainText'].split(' ')[0].replace(',', '.'))
                    unit  = extraBalance['summary/mainText'].split(' ')[1]        

                    outputDict[oneContract['phonenum']] = {
                        "extra" : extra,
                        "unit"  : unit,
                        "date"  : extraBalance['date']
                    }
                    #print(json.dumps(outputDict, indent=4, ensure_ascii=False))
                    #print(outputDict)
                except:
                    myprint(1, 'No Extra Balance')
                    outputDict[oneContract['phonenum']] = {
                        "extra" : 0,
                        "unit"  : "?",
                        "date"  : "?"
                    }
                continue

            if config.INTERNET:
                # Show Internet Mobile information only
                internetMobileFamily = oneContract['families']['internetMobile']

                remainAsNum = float(internetMobileFamily['summary/mainText'].split(' ')[0].replace(',', '.'))
                unit = internetMobileFamily['summary/mainText'].split(' ')[1]
                toAsNum = int(internetMobileFamily['gaugeInfo/to'].split(' ')[0])
                percent = internetMobileFamily['gaugeInfo/percent']
                used = "{:.2f}".format(toAsNum - remainAsNum)
                
                outputDict[oneContract['phonenum']] = {
                    "remain"  : remainAsNum,
                    "to"      : toAsNum,
                    "unit"    : unit,
                    "percent" : percent,
                    "used"    : float(used),
                    "expire"  : oneContract['reinitDate']
                }
        # Print collected information
        #print(json.dumps(outputDict, indent=4, ensure_ascii=False))
        #print(outputDict)
        return (outputDict)

    # Single contract requested
    if not contract in allContracts:
        return ()
        
    oneContract = allContracts[contract]

    if config.CALLS:
        # Show information about voice calls
        try:
            calls = oneContract['families']['appels']
            value = calls['appels/summary/additionalCredit']['value']
            formatted_value = time.strftime('%H:%M:%S', time.gmtime(value))                
            unit  = calls['appels/summary/additionalCredit']['unit']
            outputDict = {
                "value" : value,
                "formatted_value" : formatted_value,                    
                "unit"  : unit,
            }
        except:
            myprint(1, 'No Calls')
            outputDict = {
                "value" : 0,
                "formatted_value"  : "?",
                "unit"  : "?",
            }
        #print(json.dumps(outputDict, ensure_ascii=False))
        dtNow = datetime.now().strftime("%d/%m/%Y %H:%M:%S")
        myprint(1, '%s: voice calls returns %d' % (dtNow,outputDict["value"]))
        return(outputDict)

    if config.EXTRA_BALANCE:
        # Show information for extra balance
        try:
            extraBalance = oneContract['families']['horsForfait']
            extra = float(extraBalance['summary/mainText'].split(' ')[0].replace(',', '.'))
            unit  = extraBalance['summary/mainText'].split(' ')[1]        
            outputDict = {                
                "extra" : extra,
                "unit"  : unit,
                "date"  : extraBalance['date']
            }
        except:
            myprint(1, 'No Extra Balance')
            outputDict = {
                "extra" : 0,
                "unit"  : "?",
                "date"  : "?"
            }
        #print(json.dumps(outputDict, ensure_ascii=False))
        return(outputDict)

    if config.INTERNET:        
        internetMobileFamily = oneContract['families']['internetMobile']
        remainAsNum = float(internetMobileFamily['summary/mainText'].split(' ')[0].replace(',', '.'))
        unit        = internetMobileFamily['summary/mainText'].split(' ')[1]        
        toAsNum     = int(internetMobileFamily['gaugeInfo/to'].split(' ')[0])
        percent     = internetMobileFamily['gaugeInfo/percent']
        used        = "{:.2f}".format(toAsNum - remainAsNum)

        outputDict = {
            "remain"  : remainAsNum,
            "to"      : toAsNum,
            "unit"    : unit,
            "percent" : percent,
            "used"    : float(used),
            "expire"  : oneContract['reinitDate']
        }
        #print(json.dumps(outputDict, ensure_ascii=False))
        return(outputDict)

    
# Get contract(s) info from SOSH Server and update the local cache
def getContractsInfoFromSoshServer(dataCachePath):
    myprint(2, 'Connecting to SOSH Server')
    
    username, password = authinfo.decodeKey(config.SOSH_AUTH.encode('utf-8'))

    # If username / paswword have been provided on the command-line, use them
    try:
        a = getattr(config, 'SOSH_USERNAME')
    except:
        setattr(config, 'SOSH_USERNAME', username)
        
    try:
        a = getattr(config, 'SOSH_PASSWORD')
    except:
        setattr(config, 'SOSH_PASSWORD', password)

    if config.VERBOSE:
        print('%-15s: %s' % ('SOSH Username', config.SOSH_USERNAME))
        print('%-15s: %s' % ('SOSH Password', masked(config.SOSH_PASSWORD, 3)))

    with requests.session() as session:
        # Create connection to Sosh server, connect with given credentials
        sosh = mySoshClient.Sosh(config.SOSH_USERNAME, config.SOSH_PASSWORD, session)

        # Read current contracts information
        info = sosh.getContractsInformation()

        # Work done. Logout from server
        sosh.logout()

    # Update data cache
    res = dumpToFile(dataCachePath, info)
    if res:
        myprint(1, 'Failed to update local data cache')
    return(res)
