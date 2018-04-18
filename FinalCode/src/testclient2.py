from config import get_client_map, get_node_details, populate
from client import Client
populate()
node_details = get_node_details(1)
#print(node_details)
#c = Client('0.0.0.0',3000)
c = Client(node_details[0],node_details[1])
import server_pb2
import server_pb2_grpc
from server_pb2 import Request, GetRequest, QueryParams 

f  = "data/meso.out"

c.process(f)