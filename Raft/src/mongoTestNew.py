import pymongo
import sys
import logging
from pymongo import MongoClient
import time
import glob

con=None
MESONET_ROW_SIZE = 11
MESOWEST_MIN_ROW_SIZE = 10

def get_mongo_connection(host='localhost', port=27017):
    global con
    if con is None:
        print ("Establishing connection %s host and port %d" %(host,port))
        try:
            con = pymongo.MongoClient(host, port)
        except Exception as e:
            print (e)
            return None
    return con

def get_count_of_data(fromTS, toTS, params_json):
    return get_mongo_connection().mesowest.mesowest.find(parseParams(fromTS, toTS, params_json)).count()

def get_dates():
    return get_mongo_connection().mesowest.mesowest.distinct("date_utc")

def get_data(fromTS, toTS, offset, limit, params_json):
    content= ""
    if offset or limit:
        data =  list(get_mongo_connection().mesowest.mesowest.find(parseParams(fromTS, toTS, params_json)).skip(offset).limit(limit))
    else:
        data =  list(get_mongo_connection().mesowest.mesowest.find(parseParams(fromTS, toTS, params_json)))
    for d in data:
        content+=d['STN']+','+d['YYMMDD/HHMM']+','+str(d['MNET'])+','+str(d['SLAT'])+','+str(d['SLON'])+','+str(d['SELV'])+','\
                 +str(d['TMPF'])+','+str(d['SKNT'])+','+str(d['DRCT'])+','+str(d['GUST'])+','+str(d['PMSL'])+','+str(d['ALTI'])+','\
                 +str(d['DWPF'])+','+str(d['RELH'])+','+str(d['WTHR'])+','+str(d['P24I'])+'\n'
    return content

def parseParams(fromTS, toTS, params_json):
    query = {}
    if fromTS and toTS:
        query['timestamp_utc'] = {'$gte': fromTS, "$lt" : toTS}
    elif fromTS:
        query['timestamp_utc'] = {'$gte': fromTS}
    elif toTS:
        query['timestamp_utc'] = {"$lt" : toTS}

    if params_json:
        for singleParam in params_json:
            if singleParam['op']=='eq':
                if isinstance(singleParam['rhs'], list): 
                    query[singleParam['lhs']] = {'$in': singleParam['rhs']}
                else:
                    query[singleParam['lhs']] = singleParam['rhs']
            elif singleParam['op']=='gt':
                query[singleParam['lhs']] = {'$gte': singleParam['rhs']}
            elif singleParam['op']=='lt':
                query[singleParam['lhs']] = {'$lt': singleParam['rhs']}
    print(query)
    return query

def put_data(request):
    splittedArray = []
    bulkInsertArray = []
    content = (request.data).decode('utf-8')
    print ("Inside mongo******")
    for line in content.split('\n'):
        line = line.strip()
        print (line)
        if not line:
            continue
        splittedArray =  line.split(',')
        
        doc = {}
        
        #if len(splittedArray) > MESOWEST_MIN_ROW_SIZE and splittedArray[0] != "STN":
        if 'NULL' not in line:
            try:
                doc =  {'STN':splittedArray[0],'YYMMDD/HHMM':splittedArray[1],'MNET':float(splittedArray[2]),'SLAT':float(splittedArray[3]),
                        'SLON':float(splittedArray[4]),'SELV':float(splittedArray[5]),'TMPF':float(splittedArray[6]),'SKNT':float(splittedArray[7]),
                        'DRCT':float(splittedArray[8]),'GUST':float(splittedArray[9]),'PMSL':float(splittedArray[10]),'ALTI':float(splittedArray[11]),
                        'DWPF':float(splittedArray[12]),'RELH':float(splittedArray[13]),'WTHR':float(splittedArray[14]),'P24I':float(splittedArray[14]),
                        'date_utc':(splittedArray[1].split(' '))[0].replace('-',''),'timestamp_utc':
                            int(time.mktime(time.strptime(splittedArray[1], '%Y-%m-%d %H:%M:%S')))*1000}
                bulkInsertArray.append(doc)
            except:
                print("Exception while inserting to mongo")
                
            

        else:
            """
               Sample data: 
               # id,name,mesonet,lat,lon,elevation,agl,cit,state,country,active
               UIUC,2005-06-21 08:00:00,NULL,gpsmet,40.099998474121094,-88.22000122070312,NULL,NULL,NULL,NULL,NULL,NULL,NULL,NULL,NULL,NULL
               UIUC,2005-06-21 08:00:00,NULL,gpsmet,40.099998474121094,-88.22000122070312,NULL,NULL,NULL,NULL,NULL,NULL,NULL,NULL,NULL,NULL

            """
            # TODO need to fix the timestamp once clear about client stream data
            # Need to get the timestamp_utc from request
            
            try:
                doc =  {'STN': splittedArray[0],'YYMMDD/HHMM':splittedArray[1] ,'MNET': None,'SLAT':float(splittedArray[3]),'SLON':float(splittedArray[4]),
                    'SELV': float(splittedArray[5]),'TMPF': None,'SKNT': None,'DRCT': None,'GUST': None,'PMSL': None,'ALTI': None,
                    'DWPF': None,'RELH': None,'WTHR': None,'P24I': None,'date_utc':(splittedArray[1].split(' '))[0].replace('-',''),
                    'timestamp_utc':int(time.mktime(time.strptime(splittedArray[1], '%Y-%m-%d %H:%M:%S')))*1000}
            except:
                print("Exception while inserting to mesonet")
            
            if doc:
                bulkInsertArray.append(doc)
    if bulkInsertArray:
        get_mongo_connection().mesowest.mesowest.insert_many(bulkInsertArray)
    return True

    
if __name__ == '__main__':
    params_json = [{'lhs':'TMPF','op':'eq','rhs':'-9999.00'},{'lhs':'GUST','op':'gt','rhs':'7'},{'lhs':'GUST','op':'lt','rhs':'10'},{'lhs':'STN','op':'eq','rhs':['BULLF','KCKP']}]
    print(get_count_of_data(1328151000000, 2483228800000, {}))
    print(get_data(1328151000000, 2483228800000, 0, 100, {}))
    #print(get_dates())

    '''
    class Req():
        def __init__(self):
            pass
    request= Req()
    request.data="BULLF,2018-03-16 21:45:00,8.00,37.52,-110.73,1128.00,-9999.00,6.33,-9999.00,8.26,-9999.00,-9999.00,-9999.00,-9999.00,-9999.00,-9999.00\nBULLF,2012-02-01 18:15:00,8.00,37.52,-110.73,1128.00,41.00,1.62,168.80,2.86,-9999.00,-9999.00,-90.26,0.07,-9999.00,-9999.00\nBULLF,2012-02-01 18:30:00,8.00,37.52,-110.73,1128.00,41.55,1.23,151.10,2.70,-9999.00,-9999.00,-89.99,0.07,-9999.00,-9999.00\nBULLF,2012-02-01 18:45:00,8.00,37.52,-110.73,1128.00,41.96,1.88,161.00,5.10,-9999.00,-9999.00,-89.79,0.07,-9999.00,-9999.00"
    request.data = request.data.encode("utf-8")
    put_data(request)
    '''