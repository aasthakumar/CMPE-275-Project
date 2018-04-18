import glob
import gzip
import shutil
from chunktest import process
from config import get_client_map, get_node_details, populate
from client import Client
import server_pb2
import server_pb2_grpc
from server_pb2 import Request, PutRequest, QueryParams, DatFragment

populate()
c = Client('127.0.0.1',3000)

list_of_files = glob.glob('./data/*.gz')
for file_name in list_of_files:
	with gzip.open(file_name, 'rb') as f_in:
		with open(file_name[:-3], 'wb') as f_out:
			shutil.copyfileobj(f_in, f_out)

list_of_files = glob.glob('./data/*.out')
for file_name in list_of_files:
	f = open(file_name)
	c.process(file_name)