import pymongo
import sys

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



def get_count_of_data(from_timestamp, to_timestamp):
    data = get_mongo_connection().mesowest.mesowest.find({ "timestamp" : { "$gt" :  from_timestamp, "$lt" : to_timestamp}})
    return data.count()

def get_data(from_timestamp, to_timestamp, offset, limit):
    query = get_mongo_connection().mesowest.mesowest.find({ "timestamp" : { "$gt" :  from_timestamp, "$lt" : to_timestamp}})
    if offset or limit:
        data = list(query.skip(offset).limit(limit))
    else:
        data = list(query)
    print(type(data))
    return data
    
    
if __name__ == '__main__':
    (get_data(1328114400000, 1328155200000,0,30000))



