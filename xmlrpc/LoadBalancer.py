from xmlrpc.server import SimpleXMLRPCServer
from xmlrpc.server import SimpleXMLRPCRequestHandler
from xmlrpc.client import ServerProxy
import subprocess
import sys

"""
Modes:
  - 0: single node
  - 1: multiple-node static
  - 2: multiple-node dynamic
"""
OPERATION_MODE = argv[1]
NODES_FOR_MULTIPLE_STATIC = int(argv[2])

LOAD_BALANCER_PORT = 7999
LOAD_BALANCER_IP = "127.0.0.1"
LOAD_BALANCER_URL = str(LOAD_BALANCER_IP) + str(LOAD_BALANCER_PORT)
BASE_INSULT_SERVER_PORT = 8000
BASE_FILTER_SERVER_PORT =9000
BASE_SERVER_URL = "127.0.0.1"

_InsultNodeList = []
_FilterNodeList = []

# TODO: metodo de la classe nodo que te devuelva el proximo servidor a usar
class InsultNode:
    def __init__(self, server):
        self.server = server
        _InsultNodeList.append(self)
        self.working = false

class FilterNode:
    def __init__(self, server):
        self.server = server
        _FilterNodeList.append(self)
        self.working = false

def __init__():
    match OPERATION_MODE:
        case 0, 2:
            subprocess.Popen([sys.executable, 'InsultService/InsultServer.py', BASE_INSULT_SERVER_PORT])
            InsultNode(BASE_INSULT_SERVER_PORT)
            subprocess.Popen([sys.executable, 'InsultFilter/InsultFilterServer.py', LOAD_BALANCER_URL, BASE_FILTER_SERVER_PORT])
            FilterNode(BASE_FILTER_SERVER_PORT)
        case 1:
            for i in range(NODES_FOR_MULTIPLE_STATIC):
                subprocess.Popen([sys.executable, 'InsultService/InsultServer.py', BASE_INSULT_SERVER_PORT + i])
                InsultNode(BASE_INSULT_SERVER_PORT + i)
                subprocess.Popen([sys.executable, 'InsultFilter/InsultFilterServer.py', LOAD_BALANCER_URL, BASE_FILTER_SERVER_PORT + i])
                FilterNode(BASE_FILTER_SERVER_PORT + i)
        case _:
            print('Invalid OPERATION_MODE (0: single-node, 1: multiple-node static, 2: multiple - node dynamic)')
            sys.exit(-1)

# Restrict to a particular path
class RequestHandler(SimpleXMLRPCRequestHandler):
    rpc_paths = ('/RPC2',)

# Create server
with SimpleXMLRPCServer((LOAD_BALANCER_IP, LOAD_BALANCER_PORT), requestHandler=RequestHandler, allow_none=True) as server:
    # TODO: para cada metodo poner que llame a la clase nodo, pida un servidor y le pase al servidor la llamada
    def add_insult(insult):
        return None
    server.register_function(add_insult, 'add')

    def get_insults():
        return None
    server.register_function(get_insults, 'get')

    def insult_me():
        return None
    server.register_function(insult_me, 'insult')

    def subscribe_insults(subscriber_url):
        return None
    server.register_function(subscribe_insults, 'subscribe')