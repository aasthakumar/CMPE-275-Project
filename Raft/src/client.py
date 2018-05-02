import grpc
import server_pb2_grpc
import server_pb2
import config
from sys import argv
import logger as lg
import time
import chunktest
import requests
import pylibmc #for mac
#import memcache   #for windows

#mc = pylibmc.Client(["127.0.0.1:11211"], binary=True,behaviors={"tcp_nodelay": True,"ketama": True})  #for mac
#mc = memcache.Client(['127.0.0.1:11211'], debug=0)   #for windows

logger = lg.get_logger()

heartbeat_interval =2
bloom_filter_interval = 5*60

class Client():
    
    def __init__(self, host, port):
        self.channel = grpc.insecure_channel('%s:%d' % (host, port))
        self.stub = server_pb2_grpc.CommunicationServiceStub(self.channel)
        self.port = port
        self.host = host
        
    def getClientStatus(self, requested_by=0):
        req = (server_pb2.ReplicationRequest(id=requested_by))
        return self.stub.getClientStatus(req)
    
    def pingInternal(self):
        return self.stub.pingInternal(server_pb2.LeaderRequest(data="empty"))
    
    def setLeader(self,leader_id):
        return self.stub.setLeader(server_pb2.ReplicationRequest(id=leader_id))
    
    def requestVote(self, node_id):
        return self.stub.requestVote(server_pb2.ReplicationRequest(id=node_id))
    
    def getLeaderNode(self, node_id):
        return self.stub.getLeaderNode(server_pb2.ReplicationRequest(id=node_id))
    
    def getHandler(self, from_timestamp, to_timestamp):
        req = server_pb2.Request(
            fromSender=self.host,
        getRequest=server_pb2.GetRequest(
            metaData=server_pb2.MetaData(uuid=''),
            queryParams=server_pb2.QueryParams(from_utc=from_timestamp,to_utc=to_timestamp))
        )
        for stream in self.stub.getHandler(req):
            yield(stream)
            
    def GetFromLocalCluster(self, from_timestamp, to_timestamp):
        req = server_pb2.Request(
            fromSender=self.host,
        getRequest=server_pb2.GetRequest(
          metaData=server_pb2.MetaData(uuid=''),
          queryParams=server_pb2.QueryParams(from_utc=from_timestamp,to_utc=to_timestamp))
        )
        for stream in self.stub.GetFromLocalCluster(req):
            yield(stream)
            
    def putHandler(self, putData):
        return self.stub.putHandler(self.create_streaming_request_for_local_put(putData))

    def streamFile(self,file_path):
        return self.stub.putHandler(self.create_streaming_request(file_path))
    
    def create_streaming_request(self,file):
        for x in chunktest.process(None,request=False,name=file):
            req = server_pb2.Request(
                fromSender=self.host,
            putRequest=server_pb2.PutRequest(
              metaData=server_pb2.MetaData(uuid=''),
              datFragment=server_pb2.DatFragment(data= str("".join(x)).encode(encoding='utf_8'))
            ))
            yield req
            
    def create_streaming_request_for_local_put(self, data):
        req = server_pb2.Request(
            fromSender=self.host,
        putRequest=server_pb2.PutRequest(
          metaData=server_pb2.MetaData(uuid=''),
          datFragment=server_pb2.DatFragment(data= str(data).encode(encoding='utf_8'))
        ))
        yield req
        
    
    def PutToLocalCluster(self, putData):
        return self.stub.PutToLocalCluster(self.create_streaming_request_for_local_put(putData))
    
    
    def process(self, file):
        for x in chunktest.process(None,request=False,name=file):
            (self.putHandler("".join(x)))
            
    def ping(self,data_msg=""):
        req = server_pb2.Request(
            ping=server_pb2.PingRequest(
            msg = data_msg
        ))
        return self.stub.ping(req)
    
    def getUniqueDateIds(self):
        dates = self.stub.getUniqueDateIds(server_pb2.EmptyRequest())
        return dates
    
    def updateBloomFilter(self):
        return self.stub.updateBloomFilter(server_pb2.EmptyRequest())


def run():
    global host
    config.populate()
    node_id = config.get_node_id()
    node_details = config.get_node_details(node_id)
    logger.info("Connecting to host {} on port {}".format(node_details[0], node_details[1]))
    c = Client(node_details[0],node_details[1])
    c.updateBloomFilter()
    leader_node = 0
    heart_beat_count = 0
    requests.get("http://cmpe275-spring-18.mybluemix.net/delete/"+(config.get_node_details(node_id))[0])
    while(True):
        time.sleep(heartbeat_interval)
        heart_beat_count+=1
        leader = c.getLeaderNode(node_id)
        if leader_node != leader.id and leader.id == node_id:
            if leader_node != 0:
                requests.get("http://cmpe275-spring-18.mybluemix.net/delete/"+config.get_node_details(leader_node)[0])
            requests.get("http://cmpe275-spring-18.mybluemix.net/put/"+config.get_node_details(leader.id)[0])
            leader_node = leader.id
            logger.info("Publish node_id {} to external cluster".format(node_id))
            if heart_beat_count*heartbeat_interval==bloom_filter_interval:
                c.updateBloomFilter()
                



if __name__ == "__main__":
    run()
