from xmlrpc.server import SimpleXMLRPCServer, SimpleXMLRPCRequestHandler
from xmlrpc.client import ServerProxy
import subprocess
import sys

# Modes:
#   0: single-node
#   1: multiple-node static
#   2: multiple-node dynamic
OPERATION_MODE = int(sys.argv[1])
NODES_FOR_MULTIPLE_STATIC = int(sys.argv[2]) if len(sys.argv) > 2 else 1

LOAD_BALANCER_PORT = 7999
LOAD_BALANCER_IP = "127.0.0.1"
BASE_SERVER_HOST = "127.0.0.1"
BASE_INSULT_SERVER_PORT = 8000
BASE_FILTER_SERVER_PORT = 29000

# Global lists of nodes
_InsultNodeList = []
_FilterNodeList = []

dynamic_insult_index = 0
static_insult_index = 0
static_filter_index = 0

class InsultNode:
    def __init__(self, port):
        self.port = port
        self.working = False
        _InsultNodeList.append(self)

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
def spawn_filter_node(insult_node_port):
    port = BASE_FILTER_SERVER_PORT + len(_FilterNodeList)
    insult_url = f"http://{BASE_SERVER_HOST}:{insult_node_port}"
    subprocess.Popen([sys.executable, 'InsultFilter/InsultFilterServer.py', insult_url, str(port)])
    return FilterNode(port)

# Initialize nodes based on the selected mode
def initialize_nodes():
    if OPERATION_MODE in (0, 2):
        # single-node or dynamic: start one of each
        node = spawn_insult_node()
        spawn_filter_node(node.port)
    elif OPERATION_MODE == 1:
        # multiple static: start fixed number of pairs
        for i in range(NODES_FOR_MULTIPLE_STATIC):
            port_i = BASE_INSULT_SERVER_PORT + i
            subprocess.Popen([sys.executable, 'InsultService/InsultServer.py', str(port_i)])
            node = InsultNode(port_i)
            fport = BASE_FILTER_SERVER_PORT + i
            insult_url = f"http://{BASE_SERVER_HOST}:{port_i}"
            subprocess.Popen([sys.executable, 'InsultFilter/InsultFilterServer.py', insult_url, str(fport)])
            FilterNode(fport)
    else:
        print('Invalid OPERATION_MODE (0, 1, 2)')
        sys.exit(-1)

# Round-robin or dynamic selection for insult nodes
def get_insult_node():
    global static_insult_index
    if OPERATION_MODE == 1 and _InsultNodeList:
        node = _InsultNodeList[static_insult_index % len(_InsultNodeList)]
        static_insult_index += 1
        return node
    elif OPERATION_MODE == 0 and _InsultNodeList:
        return _InsultNodeList[0]
    elif OPERATION_MODE == 2:
        for node in _InsultNodeList:
            if not node.working:
                return node
        return spawn_insult_node()
    else:
        raise RuntimeError("No insult nodes available")

# Round-robin or dynamic selection for filter nodes
def get_filter_node():
    global static_filter_index
    if OPERATION_MODE == 1 and _FilterNodeList:
        node = _FilterNodeList[static_filter_index % len(_FilterNodeList)]
        static_filter_index += 1
        return node
    elif OPERATION_MODE == 0 and _FilterNodeList:
        return _FilterNodeList[0]
    elif OPERATION_MODE == 2:
        for node in _FilterNodeList:
            if not node.working:
                return node
        # Link new filter node to a newly spawned insult node
        insult_node = spawn_insult_node()
        return spawn_filter_node(insult_node.port)
    else:
        raise RuntimeError("No filter nodes available")

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

    def add_insult(insult):
        node = get_insult_node()
        node.working = True
        try:
            url = f"http://{BASE_SERVER_HOST}:{node.port}"
            client = ServerProxy(url, allow_none=True)
            return client.add(insult)
        finally:
            node.working = False
    server.register_function(add_insult, 'add')

    def get_insults():
        node = get_insult_node()
        url = f"http://{BASE_SERVER_HOST}:{node.port}"
        client = ServerProxy(url, allow_none=True)
        return client.get()
    server.register_function(get_insults, 'get')

    def insult_me():
        node = get_insult_node()
        url = f"http://{BASE_SERVER_HOST}:{node.port}"
        client = ServerProxy(url, allow_none=True)
        return client.insult()
    server.register_function(insult_me, 'insult')

    def subscribe_insults(subscriber_url):
        results = []
        for node in _InsultNodeList:
            try:
                client = ServerProxy(f"http://{BASE_SERVER_HOST}:{node.port}", allow_none=True)
                results.append(client.subscribe(subscriber_url))
            except Exception as e:
                print(f"Subscribe error on node {node.port}: {e}")
                results.append(False)
        return all(results)
    server.register_function(subscribe_insults, 'subscribe')

    print(f"Load balancer active on http://{LOAD_BALANCER_IP}:{LOAD_BALANCER_PORT}")
    server.serve_forever()
