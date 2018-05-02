from random import randint
import time
from client import Client
from config import get_client_map
import logger as lg
import math

logger = lg.get_logger()

class Server():
    def __init__(self, node_id):
        self.id = node_id
        self.status = 'FOLLOWER'  
        self.leader_id = None
        self.election_timeout = randint(1000,5000)/1000
        self.start_time = time.clock()
        self.vote_count = 0
        self.clients = {}
        self.voted = False
        self.bloomfilter = None
        self.term_count = 0
    
    
    def getLeaderId(self):
        if self.leader_id is None:
            return 0
        return self.leader_id
    
    def is_leader(self):
        if self.leader_id == self.id:
            return True
        return False
    
    def setLeaderId(self,id):
        self.leader_id = id
    
    def connect_neighbours(self):
        for v in get_client_map().items():
            node_details = v[1]
            try:
                c =Client(node_details[0], node_details[1])
                self.clients[v[0]] = {'client_obj':c,'active':True,'host':node_details[0],'port':node_details[1],'write_capacity_full':False}
            except:
                self.clients[v[0]] = {'client_obj':None,'active':False,'host':node_details[0],'port':node_details[1],'write_capacity_full':False}
    
    
    def get_client(self,node_id):
        client_obj = self.clients.get(node_id)['client_obj']
        if client_obj is None or self.clients.get(node_id)['active'] ==False:
            #If none check whether connected again
            try:
                client_obj = Client(self.clients.get(node_id)['host'],self.clients.get(node_id)['port'])
                if client_obj.pingInternal():
                    (self.clients.get(node_id))['client_obj'] = client_obj
                    (self.clients.get(node_id))['active'] = True
            except:
                logger.info("Node {} not reachable".format(node_id))
                return None
        else:
            try:
                #check whether active
                (self.clients.get(node_id))['client_obj'] = None
                (self.clients.get(node_id))['active'] = False
                if client_obj.pingInternal():
                    (self.clients.get(node_id))['client_obj'] = client_obj
                    (self.clients.get(node_id))['active'] = True
            except:
                logger.info("Node {} not reachable".format(node_id))
                return None
        return client_obj
                
    
    def get_active_node_ids(self):
        active_nodes = []
        for k in self.clients.items():
            if self.get_client(k[0]):
                active_nodes.append(k[0])
        return active_nodes
    
    def get_active_node_ids_for_push(self):
        active_nodes = []
        for k in self.clients.items():
            if self.get_client(k[0]) and not k[1].get('write_capacity_full'):
                active_nodes.append(k[0])
        return active_nodes
    
    def markNodeAsFull(self,node_id):
        node_details = self.clients.get(node_id)
        if node_details:
            node_details['write_capacity_full'] = True 
                
    
    def getActiveNodes(self):
        count = 0
        for k in get_client_map().items():
            if self.get_client(k[0]):
                count+=1   
        return count
    
    
    def checkClusterForLeader(self):
        for k in get_client_map().items():
            c = self.get_client(k[0])
            if not c:
                continue
            status = c.getClientStatus()
            logger.info("Status for client id %d",k[0])
            if(status.is_leader):
                leader_node = status.leader_id
                leader_client = self.get_client(leader_node)
                if leader_client.pingInternal():
                    return leader_node
                else:
                    logger.info("Unable to ping leader")
                    return 0
        return 0
    
    def broadCastLeader(self):
        for k in get_client_map().items():
            logger.info("Broadcasting leader node {} to cluster node {}".format(self.leader_id,k[1]))
            c = self.get_client(k[0])
            if not c:
                continue
            c.setLeader(self.leader_id)

    def start_election(self):
        while(True):
            logger.info("Sleeping for {}".format(self.election_timeout))
            time.sleep(self.election_timeout)
            if self.requestVote():
                self.setLeaderId(self.id)
                self.vote_count = 0
                self.status = "LEADER"
                self.broadCastLeader()
                return self.leader_id
            else:
                leader_node = self.checkClusterForLeader()
                if leader_node>0:
                    self.setLeaderId(leader_node)
                    self.status = "FOLLOWER"
                    return self.leader_id
                self.election_timeout = randint(1000,5000)/1000
    
    
    def getLeaderNode(self):
        if self.leader_id:
            if self.leader_id==self.id:
                return self.leader_id
            
            leader_client = self.get_client(self.leader_id)
            try:
                if leader_client is None or not leader_client.pingInternal():
                    raise
            except:
                leader_id = self.start_election()
                self.setLeaderId(leader_id)
            return self.leader_id
        else:
            logger.info("Node doesn't know about leader.Asking cluster!!!")
            leader_id = self.checkClusterForLeader()
            if leader_id == 0:
                leader_id = self.start_election()
        self.setLeaderId(leader_id)
        return self.leader_id
                    
        
    
    def requestVote(self):
        logger.info("Node {} contesting election".format(self.id))
        self.status = 'CANDIDATE'
        self.vote_count = 1
        for k in get_client_map().items():
            c = self.get_client(k[0])
            if not c:
                continue
            id = k[0]
            if id == self.id:
                logger.info("Not requesting vote from myself")
                continue
            if (c.requestVote(self.id)).result:
                self.vote_count+=1
        
        active_nodes = self.getActiveNodes()
        
        logger.info("Active nodes count %d",active_nodes)
        logger.info("No of votes needed %d" ,math.ceil((active_nodes+1)/2))
        
        if self.vote_count >= math.ceil((active_nodes+1)/2):
            return True
        else:
            return False
    
    
    def giveVote(self,id):
        if self.leader_id:
            leader_client = self.get_client(self.leader_id)
            if leader_client and leader_client.pingInternal():
                return False
        if self.status in  ("LEADER",'CANDIDATE') or self.voted:
            logger.info("Not giving vote to node %d",id)
            return False
        logger.info("Giving vote to node %d",id)
        self.voted = True
        return True
    
