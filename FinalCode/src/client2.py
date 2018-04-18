import grpc
import server_pb2_grpc
import server_pb2
import config
from sys import argv
import logger as lg
import time

logger = lg.get_logger()

heartbeat_interval =2

class Client():
    
    def __init__(self, host, port):
        self.channel = grpc.insecure_channel('%s:%d' % (host, port))
        self.stub = server_pb2_grpc.CommunicationServiceStub(self.channel)
        self.port = port
        
    def getClientStatus(self, requested_by=0):
        req = (server_pb2.ReplicationRequest(id=requested_by))
        print(req)
        return self.stub.getClientStatus(req)
        


def run():
    c = Client('0.0.0.0',3000)
    c.getClientStatus()


if __name__ == "__main__":
    run()
