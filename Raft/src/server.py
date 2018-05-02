from concurrent import futures
import time
import grpc
import server_pb2
import server_pb2_grpc
import sys
from Node import Server
import logger as lg
import mongoTestNew
from utils import getEpochTime
import config
from client import Client
import json
from threading import Thread
from queue import Queue
from createbloomfilter import CreateBloomFilter
import requests
import time
import datetime

q = Queue(maxsize=0)
dqueue = []
_ONE_DAY_IN_SECONDS = 60 * 60 * 24
encoding = "UTF-8"
server_port = None
node_id = None
space = None
logger = None

class RequestHandler(server_pb2_grpc.CommunicationServiceServicer):
    def __init__(self):
        self.node = Server(node_id)
        self.node.connect_neighbours()
    
    def pingInternal(self,request, context):
        return server_pb2.BoolResponse(result=True)
    
    def getClientStatus(self,request, context):
        return server_pb2.ClientResponse(id= self.node.id, is_leader = self.node.is_leader(),leader_id = self.node.getLeaderId())
    
    def setLeader(self, request, context):
        logger.info("Setting leader %d",request.id)
        self.node.leader_id = request.id
        self.node.voted = False
        return server_pb2.BoolResponse(result=True)
        
    def requestVote(self, request, context):
        logger.info("Requesting vote %d",request.id)
        res = self.node.giveVote(request.id)
        return server_pb2.BoolResponse(result=res)
    
    def getLeaderNode(self,request, context):
        leader_node = self.node.getLeaderNode()
        logger.info("leader node for node-id {} is {}".format(str(self.node.id), str(leader_node)))
        return server_pb2.ReplicationRequest(id=leader_node)
    
    def getHandler(self, request, context):
        #checking bloomfilter
        d = int(time.mktime(time.strptime(request.getRequest.queryParams.from_utc, '%Y-%m-%d %H:%M:%S')))
        toDate = int(time.mktime(time.strptime(request.getRequest.queryParams.to_utc, '%Y-%m-%d %H:%M:%S')))
        process_internal = False

        while d <= toDate:
            date_to_check = (datetime.datetime.fromtimestamp(d).strftime('%Y%m%d'))
            c = self.node.bloomfilter
            if c.testdate(date_to_check):
                process_internal = True
                break
            d += (24*60*60)
        
        if process_internal:
            serverlist=self.node.get_active_node_ids()
            return_queue = Queue(maxsize=0)
            for node_id in serverlist:
                assign_to_node = (Thread(target=self.connect_to_node, args =(node_id,request,return_queue,)))
                assign_to_node.setDaemon(True)
                assign_to_node.start()
            
            null_count = 0        
            while(True):
                if (return_queue.qsize()):
                    d = return_queue.get()
                    if not d:
                        null_count+=1
                        continue
                    if request.fromSender =="external-client":
                        yield(provideJson(d))
                    else:
                        yield(d)
                
                if null_count==len(serverlist):
                    break
        else:
            if request.fromSender =="external-client":
                #external_hosts = requests.get("http://cmpe275-spring-18.mybluemix.net/get").text
                external_hosts = "169.254.149.215"
                external_hosts = external_hosts.split(",")
                request.fromSender = ""
                leader_details = config.get_node_details(self.node.leader_id)
                return_queue_external = Queue(maxsize=0)
                for host_details in external_hosts:
                    if host_details==leader_details[0]:
                        continue
                    assign_to_node = (Thread(target=self.connect_to_external_node, args =(host_details,request,return_queue_external,)))
                    assign_to_node.setDaemon(True)
                    assign_to_node.start()
                null_count = 0
                while(True):
                    if (return_queue_external.qsize()):
                        d = return_queue_external.get()
                        if not d:
                            null_count+=1
                            continue
                        yield(provideJson(d))
                    
                    if null_count==len(external_hosts)-1:
                        break
               
    def connect_to_external_node(self, host_details,request,return_queue):
        try:
            client = Client(host=host_details,port=8080)
            stream = client.getHandler(request.getRequest.queryParams.from_utc, request.getRequest.queryParams.to_utc)
            for res in stream:
                if res.datFragment.data:
                    return_queue.put(res)
        finally:
            return_queue.put(None)
            
    def connect_to_node(self, node_id,request,return_queue):
        client = self.node.get_client(node_id)
        if client is not None:
            stream = client.GetFromLocalCluster(request.getRequest.queryParams.from_utc, request.getRequest.queryParams.to_utc)
            for res in stream:
                if res.datFragment.data:
                    return_queue.put(res)
        return_queue.put(None)    
        
    def GetFromLocalCluster(self, request, context):
        fromTimestamp = getEpochTime(request.getRequest.queryParams.from_utc)
        toTimestamp = getEpochTime(request.getRequest.queryParams.to_utc)
        data_count = mongoTestNew.get_count_of_data(fromTimestamp, toTimestamp, request.getRequest.queryParams.params_json)
        offset = 0 
        limit = 2000
        yield_count = 1
        while(offset<=data_count):
            query_data = mongoTestNew.get_data(fromTimestamp, toTimestamp, offset, limit, request.getRequest.queryParams.params_json)
            response = server_pb2.Response(code=1,
                                       metaData = server_pb2.MetaData(uuid="",numOfFragment=int(data_count)),
                                       datFragment = server_pb2.DatFragment(timestamp_utc="",data=str(query_data).encode(encoding='utf_8'))
                                       )
            yield_count+=1
            yield (response)
            offset = offset+limit
            
    def pushDataToNode(self,req,node_id):
        client = self.node.get_client(node_id)
        res = client.PutToLocalCluster((req.putRequest.datFragment.data).decode('utf-8'))
        if res.code!=1:
            return False
        return True   
    
    def pushDataToExternalCluster(self,req):
        #external_hosts = requests.get("http://cmpe275-spring-18.mybluemix.net/get").text
        external_hosts = "169.254.230.239"
        external_hosts = external_hosts.split(",")
        req.fromSender = ""
        leader_details = config.get_node_details(self.node.leader_id)
        
         
        for host_details in external_hosts:
            if host_details==leader_details[0]:
                continue
            
            try:
                client = Client(host=host_details,port=8080)
                res = client.putHandler((req.putRequest.datFragment.data).decode('utf-8'))
                if res.code==1:
                    break
            except Exception as e:
                print(e)
                
                
            
            
            
    
            
    def putHandler(self, request_iterator, context):
        serverlist=self.node.get_active_node_ids_for_push()
        st_idx = 0
        
        
        counter = 0
        for req in request_iterator:
                if counter%3==0 or not serverlist:
                    self.pushDataToExternalCluster(req)
                    counter = counter+1
                    continue
                
                if not serverlist:
                    return server_pb2.Response(code=2)
                node_id = serverlist[st_idx]
                while(True):
                    if self.pushDataToNode(req, node_id):
                        st_idx=st_idx+1
                        if st_idx > len(serverlist)-1:
                            st_idx=0
                        break
                    else:
                        self.node.markNodeAsFull(node_id)
                        serverlist.pop(st_idx)
                        if not serverlist:
                            return server_pb2.Response(code=2)
                        if st_idx > len(serverlist)-1:
                            st_idx=0
                        node_id = serverlist[st_idx]
                counter+=1
                
        return server_pb2.Response(code=1)
    
    def PutToLocalCluster(self, request_iterator, context):
        for req in request_iterator:
            if(mongoTestNew.get_mongo_connection().mesowest.command("dbstats")["dataSize"] > space):
                return server_pb2.Response(code=2)
            mongoTestNew.put_data(req.putRequest.datFragment)
        return server_pb2.Response(code=1)    
    
    def ping(self,req, context):
        return server_pb2.Response(code=1)
    
    def getUniqueDateIds(self,request, context):
        data = mongoTestNew.get_dates()
        
        dates = server_pb2.DateResponse()
        for d in data:
            d_t = dates.dates.add()
            d_t.date = d
        return dates
    
    def updateBloomFilter(self, request, context):
        nodeids = self.node.get_active_node_ids()
        dates_set = set()
        for node in nodeids:
            client = self.node.get_client(node)
            if client is None:
                continue
            data = client.getUniqueDateIds()
            for d in data.dates:
                dates_set.add(d.date)
        c = CreateBloomFilter(len(dates_set),dates_set)
        self.node.bloomfilter = c
        return server_pb2.BoolResponse(result=True)

def run(host, port, node):
    global server_port
    global node_id
    global logger
    node_id = node
    server_port = port
    server = grpc.server(futures.ThreadPoolExecutor(max_workers=10))
    server_pb2_grpc.add_CommunicationServiceServicer_to_server(RequestHandler(), server)
    server.add_insecure_port('%s:%d' % (host, port))
    server.start()
    logger = lg.get_logger()

    try:
        while True:
            logger.info("Server started at....%d", port)
            time.sleep(_ONE_DAY_IN_SECONDS)
    except KeyboardInterrupt:
        server.stop(0)

def provideJson(chunk):
    jsonChunk = []
    for dline in (chunk.datFragment.data).decode('utf-8').strip('\n').split('\n'):
        dlineValues = dline.replace('"',"'").split(',')
        dlineJsonValues = {
            'STN':dlineValues[0],
            'TIMESTAMP':dlineValues[1],
            'MNET':dlineValues[2],
            'SLAT':dlineValues[3],
            'SLON':dlineValues[4],
            'SELV':dlineValues[5],
            'TMPF':dlineValues[6],
            'SKNT':dlineValues[7],
            'DRCT':dlineValues[8],
            'GUST':dlineValues[9],
            'PMSL':dlineValues[10],
            'ALTI':dlineValues[11],
            'DWPF':dlineValues[12],
            'RELH':dlineValues[13],
            'WTHR':dlineValues[14],
            'P24I':dlineValues[15]
        }
        jsonChunk.append(json.dumps(dlineJsonValues))
    responseChunk = server_pb2.Response(code=1,
                                       metaData = server_pb2.MetaData(uuid="",numOfFragment=int(chunk.metaData.numOfFragment)),
                                       datFragment = server_pb2.DatFragment(timestamp_utc="",data=str((',').join(jsonChunk)).encode(encoding='utf_8'))
                                       )
    return responseChunk
        

if __name__ == '__main__':
    config.populate()
    node_id = config.get_node_id()
    node_details = config.get_node_details(node_id)
    space = config.get_space()
    run(node_details[0],node_details[1],node_id)