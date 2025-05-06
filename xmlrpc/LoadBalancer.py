from xmlrpc.server import SimpleXMLRPCServer, SimpleXMLRPCRequestHandler
from xmlrpc.client import ServerProxy
import subprocess
import sys
import time
import math
import threading

# Modes:
#   0: single-node
#   1: multiple-node static (default 2 nodes)
#   2: multiple-node dynamic
OPERATION_MODE = int(sys.argv[1])
NODES_FOR_MULTIPLE_STATIC = int(sys.argv[2]) if len(sys.argv) > 2 else 2

LOAD_BALANCER_PORT = 7999
LOAD_BALANCER_IP = "127.0.0.1"
BASE_SERVER_HOST = "127.0.0.1"
BASE_INSULT_SERVER_PORT = 8000
BASE_FILTER_SERVER_PORT = 29000

# Dynamic scaling factors
SINGLE_NODE_CAPACITY = 100
MAX_KILL_TRIES = 15
SECONDS_BETWEEN_SCALING = 5
_avg_request_ttc = 0.05
_request_rate = 100
_last_request_count = time.time()
_new_requests = 0

# Global lists of nodes
_InsultNodeList = []
_FilterNodeList = []

_RR_insult_index = 0
_RR_filter_index = 0
_sub_node_index = 0

class InsultNode:
    def __init__(self, port):
        self.port = port
        self.working = False
        self.subs = set()
        self.avg_request_ttc = 0
        self.num_handled_requests = 0
        _InsultNodeList.append(self)
    
    def append_sub(self, subscriber_url):
        self.subs.add(subscriber_url)
    
    def remove_sub(self, subscriber_url):
        self.subs.discard(subscriber_url)
    
    def get_subs(self):
        return self.subs
    
    def register_request(self, delta):
        self.avg_request_ttc = self.num_handled_requests * self.avg_request_ttc + delta
        self.num_handled_requests += 1
        self.avg_request_ttc /= self.num_handled_requests

    def get_avg(self):
        return self.avg_request_ttc

    def get_global_avg():
        avg = 0
        for node in _InsultNodeList:
            avg += node.get_avg()
        return avg / len(_InsultNodeList)

class FilterNode:
    def __init__(self, port):
        self.port = port
        self.working = False
        _FilterNodeList.append(self)

# Spawn an insult node on next available port
def spawn_insult_node():
    port = BASE_INSULT_SERVER_PORT + len(_InsultNodeList)
    subprocess.Popen([sys.executable, 'InsultService/InsultServer.py', str(port)])
    return InsultNode(port)

# Spawn a filter node linked to a specific insult node
def spawn_filter_node(): #DEBUG|
    port = BASE_FILTER_SERVER_PORT + len(_FilterNodeList)
    insult_url = f"http://{LOAD_BALANCER_IP}:{LOAD_BALANCER_PORT}"
    subprocess.Popen([sys.executable, 'InsultFilter/InsultFilterServer.py', insult_url, str(port)])
    return FilterNode(port)

# Initialize nodes based on the selected mode
def initialize_nodes():
    if OPERATION_MODE in (0, 2):
        # single-node or dynamic: start one of each
        spawn_insult_node()
        #DEBUG|spawn_filter_node()
    elif OPERATION_MODE == 1:
        # multiple static: start fixed number of pairs
        for i in range(NODES_FOR_MULTIPLE_STATIC):
            spawn_insult_node()
            #DEBUG|spawn_filter_node()
    else:
        print('Invalid OPERATION_MODE (0, 1, 2)')
        sys.exit(-1)

# Round-robin or static selection for insult nodes
def get_node_to_sub():
    global _sub_node_index
    node = _InsultNodeList[_sub_node_index]
    _sub_node_index = (_sub_node_index + 1) % len(_InsultNodeList)
    return node

# Round-robin or static selection for insult nodes
def get_insult_node():
    global _RR_insult_index
    node = _InsultNodeList[_RR_insult_index]
    if OPERATION_MODE == 2 or OPERATION_MODE == 3:
        _RR_insult_index = (_RR_insult_index + 1) % len(_InsultNodeList)
    return node

# Round-robin or static selection for filter nodes
def get_filter_node():
    global _RR_filter_index
    node = _FilterNodeList[_RR_filter_index]
    if OPERATION_MODE == 2 or OPERATION_MODE == 3:
        _RR_filter_index = (_RR_filter_index + 1) % len(_FilterNodeList)
    return node

# If multiple-node dynamic mode specified, this method makes number of nodes scale every SECONDS_BETWEEN_SCALING seconds
def dynamic_scaler():
    global _new_requests, _last_request_count, _request_rate, _avg_request_ttc
    while True:
        _request_rate = _new_requests / _last_request_count
        _new_requests = 0
        _last_request_count = time.time()
        _avg_request_ttc = InsultNode.get_global_avg()
        needed_nodes = math.ceil(int((_request_rate * _avg_request_ttc) / SINGLE_NODE_CAPACITY))
        nodes_delta = needed_nodes - len(_InsultNodeList)
        if nodes_delta > 0:
            for i in range(nodes_delta):
                spawn_insult_node()
                #DEBUG|spawn_filter_node()
        elif nodes_delta < -1:
            kill_tries = 0
            while nodes_delta < 0 and kill_tries < MAX_KILL_TRIES:
                node = get_insult_node()
                if node.working == False:
                    _InsultNodeList.remove(node)
                    nodes_delta += 1
                    for sub in node.get_subs():
                        subscribe_insults(sub)
                    node = None
                kill_tries += 1
        time.sleep(SECONDS_BETWEEN_SCALING)

def metrics():
    global _new_requests, _last_request_count, _request_rate, _avg_request_ttc
    while True:
        _request_rate = _new_requests / _last_request_count
        _new_requests = 0
        _last_request_count = time.time()
        _avg_request_ttc = InsultNode.get_global_avg()
        needed_nodes = math.ceil(int((_request_rate * _avg_request_ttc) / SINGLE_NODE_CAPACITY))
        nodes_delta = needed_nodes - len(_InsultNodeList)
        print("------------ Metrics ------------")
        print("Avg request TTC: ", _avg_request_ttc, "s")
        print("Request rate: ", _request_rate, "req/s")
        print("Necessary nodes: ", nodes_delta, " nodes")
        time.sleep(SECONDS_BETWEEN_SCALING)

# Start initial nodes
initialize_nodes()

# Restrict RPC path
default_paths = ('/RPC2',)
class RequestHandler(SimpleXMLRPCRequestHandler):
    rpc_paths = default_paths

# Launch the XML-RPC load balancer
typical_target = (LOAD_BALANCER_IP, LOAD_BALANCER_PORT)
with SimpleXMLRPCServer(typical_target, requestHandler=RequestHandler, allow_none=True) as server:
    server.register_introspection_functions()

    def proxy_to_insult(funcName:str, attr=None):
        global _new_requests
        _new_requests = _new_requests + 1
        node = get_insult_node()
        node.working = True
        delta = time.time()
        try:
            url = f"http://{BASE_SERVER_HOST}:{node.port}"
            client = ServerProxy(url, allow_none=True)
            func = getattr(client, funcName)
            if attr is not None: return func(attr)
            else: return func()
        finally:
            node.working = False
            node.register_request(time.time() - delta)

    def add_insult(insult):
        return proxy_to_insult("add", insult)
    server.register_function(add_insult, 'add')

    def get_insults():
        return proxy_to_insult("get")
    server.register_function(get_insults, 'get')

    def insult_me():
        return proxy_to_insult("insult")
    server.register_function(insult_me, 'insult')

    def subscribe_insults(subscriber_url):
        global _new_requests
        _new_requests = _new_requests + 1
        delta = time.time()
        node = get_node_to_sub()
        url = f"http://{BASE_SERVER_HOST}:{node.port}"
        client = ServerProxy(url, allow_none=True)
        node.append_sub(subscriber_url)
        client.subscribe(subscriber_url)
        node.register_request(time.time() - delta)
    server.register_function(subscribe_insults, 'subscribe')

    def delete_subscriber(node_port, subscriber_url):
        try:
            _InsultNodeList[node_port - BASE_INSULT_SERVER_PORT].remove_sub(subscriber_url)
        except Exception:
            print("Faulty request to delete subscriber from InsultNode with port ", node_port)
    server.register_function(delete_subscriber, 'unalive')

    print(f"Load balancer active on http://{LOAD_BALANCER_IP}:{LOAD_BALANCER_PORT}")
    if OPERATION_MODE == 3: threading.Thread(target=dynamic_scaler, daemon=True).start()
    threading.Thread(target=metrics, daemon=True).start()
    server.serve_forever()