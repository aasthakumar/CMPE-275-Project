# ClimateFacts

### Requirements ###
gRPC, libmemcached, pylibmc, mmh3, bitarray, mongoDB
### Make changes to config.cfg present in raft folder to include the ip of all the nodes participating in RAFT leader election system ###
client_map = {1: ["169.254.27.153",8080],2:["169.254.40.41",8080],3:["169.254.51.179",8080],4:["169.254.18.67",8080]}
node_id = 1 -- change it to your client id (say your system is client 2 in above client map, then change it to 2)
space = 10737418240 -- change it as per your systems capacity.


### Start MongoDB services on your system ###

### Start RAFT server, which is the gRPC server. This will expose both leader election protocol as well other services required to post and get Climate Fact Data ###

python server.py (present under raft/src folder)
This will start the leader election and will select the leader.

### Start gRPC client to listen for external requests ###
python client.py

