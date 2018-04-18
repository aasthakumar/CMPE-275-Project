import configparser
import ast

config = configparser.ConfigParser()
config.read('config.cfg')
client_map = None


def populate():
    global client_map
    client_map = ast.literal_eval(config.get('DEFAULT', 'client_map'))

def get_node_id():
    return int(config.get('DEFAULT','node_id'))

def get_node_details(node_id):
    if client_map.get(node_id) is None:
        raise Exception
    return client_map.get(node_id)


def get_client_map():
    return client_map

def get_space():
    return int(config.get('DEFAULT','space'))