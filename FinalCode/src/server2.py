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

#aastha's import
from threading import Thread
from queue import Queue
from collections import deque
q = Queue(maxsize=0)

dqueue = []


_ONE_DAY_IN_SECONDS = 60 * 60 * 24
encoding = "UTF-8"

server_port = None
node_id = None

logger = None

class RequestHandler(server_pb2_grpc.CommunicationServiceServicer):
    '''
    '''
    
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
        print("Inside gethandler")
        print(request.getRequest.queryParams)
        serverlist=self.node.get_active_node_ids()
        return_queue = Queue(maxsize=0)
        for node_id in serverlist:
            print("Connecting to node",node_id)
            assign_to_node = (Thread(target=self.connect_to_node, args =(node_id,request,return_queue,)))
            assign_to_node.setDaemon(True)
            assign_to_node.start()
        
        null_count = 0        
        while(True):
            if (return_queue.qsize()):
                print("queue data ",return_queue.qsize())
                d = return_queue.get()
                if not d:
                    print("incrementing null count")
                    null_count+=1
                    continue
                yield(d)
            
            if null_count==len(serverlist):
                print ("Breaking null check")
                print ("null_count",null_count)
                print ("server list",serverlist)
                break
                
            
    def connect_to_node(self, node_id,request,return_queue):
#         channel = grpc.insecure_channel(hostdetails)
#         stub = request_pb2_grpc.CommunicationServiceStub(channel)
        client = self.node.get_client(node_id)
        print("at..." + str(node_id))
        print("Inside connect_to_node",request.getRequest.queryParams)
        #fromTimestamp = getEpochTime(request.getRequest.queryParams.from_utc)
        #toTimestamp = getEpochTime(request.getRequest.queryParams.to_utc)
        stream = client.GetFromLocalCluster(request.getRequest.queryParams.from_utc, request.getRequest.queryParams.to_utc)
        for res in stream:
            print ("inserting into queue")
            return_queue.put(res)
        return_queue.put(None)
        #print ("data count from "+str(node_id)+" is "+str(return_queue.qsize()))
    
        
    def GetFromLocalCluster(self, request, context):
        print("Inside GetFromLocalCluster")
        print((request.getRequest.queryParams))
        
        fromTimestamp = getEpochTime(request.getRequest.queryParams.from_utc)
        toTimestamp = getEpochTime(request.getRequest.queryParams.to_utc)
        
        
        #fromTimestamp, toTimestamp = 1328114400000, 1328155200000
        data_count = mongoTestNew.get_count_of_data(fromTimestamp, toTimestamp)
        print("Data count is",data_count)
        #TODO Move to config
        offset = 0 
        limit = 2000
        yield_count = 1
        while(offset<=data_count):
            query_data = mongoTestNew.get_data(fromTimestamp, toTimestamp, offset, limit)
            response = server_pb2.Response(code=1, msg="froms-1",
                                       metaData = server_pb2.MetaData(uuid="",numOfFragment=int(data_count)),
                                       datFragment = server_pb2.DatFragment(timestamp_utc="",data=str(query_data).encode(encoding='utf_8'))
                                       )
            print ("yield count",yield_count)
            yield_count+=1
            yield (response)
            offset = offset+limit
            
    def pushDataToNode(self,req,node_id):
        print ("Pusing data to ",node_id)
        client = self.node.get_client(node_id)
        res = client.PutToLocalCluster((req.putRequest.datFragment.data).decode('utf-8'))
        if res!=1:
            return False
        return True
            
            
    def putHandler(self, request_iterator, context):
        serverlist=self.node.get_active_node_ids_for_push()
        print("Inside put handler")
        
        st_idx = 0
        
        for req in request_iterator:
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
                        print ("Marking node as full ",node_id)
                        self.node.markNodeAsFull(node_id)
                        serverlist.pop(st_inx)
                
        return server_pb2.Response(code=1)
    
    def PutToLocalCluster(self, request_iterator, context):
        print ("server inside PutToLocalCluster")
        for req in request_iterator:
            print ((req.putRequest.datFragment.data).decode('utf-8'))
            mongoTestNew.put_data((req.putRequest.datFragment.data).decode('utf-8'))
        return server_pb2.Response(code=1)
    
    
    def ping(self,req, context):
        print ("Inside server ping")
        return server_pb2.Response(code=1)
    

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
        

if __name__ == '__main__':
    config.populate()
    node_id = config.get_node_id()
    node_details = config.get_node_details(node_id)
    print(node_details[0])
    print(node_details[1])
    print(type(node_details[0]))
    print(type(node_details[1]))
    run(node_details[0],node_details[1],node_id)
    
    
