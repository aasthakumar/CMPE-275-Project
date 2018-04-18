import grpc
import server_pb2_grpc
import server_pb2
from concurrent import futures
import time
import json
import sys
from queue import Queue
from threading import Thread
from collections import deque
import configparser
from createbloomfilter import CreateBloomFilter
from datetime import date

_ONE_DAY_IN_SECONDS = 60 * 60 * 24

q = Queue(maxsize=0)
return_queue = Queue(maxsize=0)
nodestoremove = []
serverlist = {}
dqueue = []
dqueue_for_read_request = deque([], maxlen=1)
bloom_filter_dic = {}
# creating a node list from config file

class Server(request_pb2_grpc.CommunicationServiceServicer):

    def __init__(self):
        print("init")

    def MessageHandler(self, request, context):
        print("in message data")
        q.put(request)
        print(q.qsize())
        while True:
            if return_queue.qsize() != 0:
                print("here in queue")
                print(return_queue.qsize())
                print(return_queue.get())
                return request_pb2.Response(isSuccess = True,msg = str(return_queue.get()))               
    
def run(host, port, q):
    '''
    Run the GRPC server
    '''
    server = grpc.server(futures.ThreadPoolExecutor(max_workers=10))
    request_pb2_grpc.add_CommunicationServiceServicer_to_server(Server(), server)
    server.add_insecure_port('%s:%d' % (host, port))
    server.start()
    try:
        while True:
            print("Server started at...%d" % port)
            time.sleep(_ONE_DAY_IN_SECONDS)
    except KeyboardInterrupt:
        server.stop(0)

def create_node_list():
    global serverlist
    global dqueue
    config = configparser.ConfigParser()
    config.read('config.cfg')
    grpc_port= config.get('Grpc_Cluster','grpc_port').split(',')
    grpc_host= config.get('Grpc_Cluster','grpc_host').split(',')
    cnt = 1
    for port, host in zip(grpc_port, grpc_host):
        servername = 'Server' + str(cnt)
        serverlist[servername] = '%s:%d' % (host, int(port))
        cnt = cnt + 1
    print(serverlist)
    dqueue = deque([], maxlen=(len(serverlist)-1))


def create_bloomfilters():
    for server, connect_details in serverlist.items():
        # create bloom filter for each to see what data it contains
       create_bloomfilter_connect(connect_details,server)


def create_bloomfilter_connect(connect_details,server):
    channel = grpc.insecure_channel(connect_details)
    stub = request_pb2_grpc.CommunicationServiceStub(channel)
        
        #might change when cassandra connection is changed
    req = request_pb2.PingRequest(msg ="in grpc")
    res = stub.GetDataInformation(req)
    ls = json.loads(res.datevalue)
    cbf = CreateBloomFilter(res.cnt,ls)
    bloom_filter_dic[server] = cbf

def string_to_date(todate):
        year,month, day = todate.split("-")
        return date(int(year), int(month), int(day))

def find_servers_for_read(request):
    # change this to read from grpc request
    dateval = "2012-02-01"
    match_list =[]
    for server, bloomfilterobj in bloom_filter_dic.items():
        if bloomfilterobj.testdate(string_to_date(dateval)) == 1:
            match_list.append(server)
    print(match_list)
    if len(match_list) == 0:
        return "no node to handle request"   
    elif len(match_list) == 1:
        host_details = serverlist[server]
    else:
        for server in match_list:
            if server not in dqueue_for_read_request:
                host_details = serverlist[server]
                dqueue_for_read_request.append(server)
                break
    return_queue.put(connect_to_node(host_details,request,server,q))

def broadcast_read_request(request):
    for server,hostdetails in serverlist.items():
        assign_to_node = (Thread(target=connect_to_node, args =(hostdetails,request,server,q,)))
        assign_to_node.setDaemon(True)
        assign_to_node.start()
        print("here........")

def execute_requests(q):
    global dqueue
    while True:
        while q.qsize() != 0:
            current_request = q.get()
            q.task_done()
            # code to send insert requests in round robin fashion
            if current_request.fromSender == "insert":
                for server,hostdetails in serverlist.items():
                    if server not in dqueue:
                        #with Pool(processes=10) as pool:                       
                        assign_to_node = (Thread(target=connect_to_node, args =(hostdetails,current_request,server,q,)))
                        assign_to_node.setDaemon(True)
                        assign_to_node.start()
                        print("here........")
                        dqueue.append(server)
                        break 
            else:
                broadcast_read_request(current_request)
                print("done")

# to remove
def connect_to_node_1(hostdetails,request,server,q):
    global dqueue
    channel = grpc.insecure_channel(hostdetails)
    stub = request_pb2_grpc.CommunicationServiceStub(channel)
    print("at..." + hostdetails)
    res = stub.GetDataInformation(request)
    if res.msg == "node full":
        nodestoremove.append(server)
        q.put(request)
        if len(nodestoremove) != 0:        
            for nodes in nodestoremove:
                serverlist.pop(nodes)
                re_intialize_queue = deque([], maxlen=(len(serverlist)-1))
                dqueue = re_intialize_queue
    else:
        return_queue.put(res)

    if request.fromSender == "insert":
        print("here")
        if res !=  "node full":
            return_queue.put(res)
            #create_bloomfilter_connect(hostdetails,server)
    print(res)
    return res
# to remove


def connect_to_node(hostdetails,request,server,q):
    global dqueue
    channel = grpc.insecure_channel(hostdetails)
    stub = request_pb2_grpc.CommunicationServiceStub(channel)
    print("at..." + hostdetails)
    res = stub.MessageHandler(request)
    if res.msg == "node full":
        nodestoremove.append(server)
        q.put(request)
        if len(nodestoremove) != 0:        
            for nodes in nodestoremove:
                serverlist.pop(nodes)
                re_intialize_queue = deque([], maxlen=(len(serverlist)-1))
                dqueue = re_intialize_queue
    else:
        print("entering in queue")
        return_queue.put(res)

    if request.fromSender == "insert":
        print("here")
        if res !=  "node full":
            return_queue.put(res)
            #create_bloomfilter_connect(hostdetails,server)
    print(res)
    return res

if __name__ == '__main__':
    cmdargs = sys.argv
    print(cmdargs[1])
    create_node_list()
    #create_bloomfilters()
    startserver = (Thread(target=run, args =('0.0.0.0', int(cmdargs[1]),q, )))
    startserver.start()
    loadbalance = (Thread(target=execute_requests, args=(q, )))
    loadbalance.start()
    