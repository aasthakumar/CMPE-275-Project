import pymongo
import sys
import logging
from pymongo import MongoClient
import time
import glob

con=None
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

def get_count_of_data(fromTS, toTS):

    #fromTS = int(time.mktime(time.strptime(from_timestamp, '%Y-%m-%d %H:%M:%S'))) * 1000
    #toTS = int(time.mktime(time.strptime(to_timestamp, '%Y-%m-%d %H:%M:%S'))) * 1000
    return get_mongo_connection().mesowest.mesowest.find({ "timestamp_utc" : { "$gt" :  fromTS, "$lt" : toTS}}).count()

def get_dates():
    return get_mongo_connection().mesowest.mesowest.distinct("date_utc")

def get_data(fromTS, toTS, offset, limit):

    #fromTS = int(time.mktime(time.strptime(from_timestamp, '%Y-%m-%d %H:%M:%S'))) * 1000
    #toTS = int(time.mktime(time.strptime(to_timestamp, '%Y-%m-%d %H:%M:%S'))) * 1000
    content= ""
    if offset or limit:
        data =  list(get_mongo_connection().mesowest.mesowest.find({ "timestamp_utc" : { "$gt" :  fromTS, "$lt" : toTS}},{'raw':1,'_id':0}).skip(offset).limit(limit))
    else:
        data =  list(get_mongo_connection().mesowest.mesowest.find({ "timestamp_utc" : { "$gt" :  fromTS, "$lt" : toTS}},{'raw':1,'_id':0}))
    
    for d in data:
        content+=d['raw']+"\n"
    return content

def put_data(content):
    splittedArray = []
    bulkInsertArray = []
    for line in content.split('\n'):
        line = line.strip()
        splittedArray =  line.split()
        if len(splittedArray)>10 and splittedArray[0]!="STN":
            singleTuple = {"station":splittedArray[0],"timestamp_utc":int(time.mktime(time.strptime(splittedArray[1], '%Y%m%d/%H%M'))) * 1000, "date_utc": splittedArray[1].split('/')[0],"raw":line}
            bulkInsertArray.append(singleTuple)

        """if len(splittedArray)>10 and splittedArray[0]!="STID":
            singleTuple = {"station":splittedArray[0],"timestamp_utc":int(time.mktime(time.strptime(splittedArray[1], '%Y%m%d/%H%M'))) * 1000, "date_utc": splittedArray[1].split('/')[0],"raw":line}
            bulkInsertArray.append(singleTuple)"""

    get_mongo_connection().mesowest.mesowest.insert_many(bulkInsertArray)
    return True
    
if __name__ == '__main__':
    #list_of_files = glob.glob('./data/*.out') 
    #for file_name in list_of_files:
    #    file = open(file_name).readlines()
    #    put_data(file)

    #print(get_count_of_data(1483228800000, 2483228800000))
    #print(get_data(1483228800000, 2483228800000,0,100))
    #put_data("  ABAUT  20120201/1900      8.00    37.84  -109.46  3453.00    19.33    10.01   207.00    15.74 -9999.00 -9999.00     3.65    49.74 -9999.00 -9999.00\n  BULLF  20120201/1815      8.00    37.52  -110.73  1128.00    41.00     1.62   168.80     2.86 -9999.00 -9999.00   -90.26     0.07 -9999.00 -9999.00\n  BULLF  20120201/1830      8.00    37.52  -110.73  1128.00    41.55     1.23   151.10     2.70 -9999.00 -9999.00   -89.99     0.07 -9999.00 -9999.00\n  BULLF  20120201/1845      8.00    37.52  -110.73  1128.00    41.96     1.88   161.00     5.10 -9999.00 -9999.00   -89.79     0.07 -9999.00 -9999.00")
    print(get_dates())