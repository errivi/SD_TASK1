from xmlrpc.server import SimpleXMLRPCServer, SimpleXMLRPCRequestHandler
from xmlrpc.client import ServerProxy
import subprocess
import sys
import time
import multiprocessing as mp

NUM_OF_NODES = int(sys.argv[1]) if int(sys.argv[1]) > 1 else 1

LOAD_BALANCER_PORT = 7999
LOAD_BALANCER_IP = "127.0.0.1"
BASE_SERVER_HOST = "127.0.0.1"
BASE_INSULT_SERVER_PORT = 8000
BASE_FILTER_SERVER_PORT = 29000

# Global lists of nodes
_InsultNodeList = []
_FilterNodeList = []
_RR_insult_index = 0
_RR_filter_index = 0
_sub_node_index = 0

_workers = []

# Test configurations
TOTAL_NUM_REQS = 500_000
NUM_OF_WORKERS = 3
REQS_PER_WORKER = int(TOTAL_NUM_REQS / (NUM_OF_NODES * NUM_OF_WORKERS))

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
def spawn_filter_node(): 
    port = BASE_FILTER_SERVER_PORT + len(_FilterNodeList)
    insult_url = f"http://{LOAD_BALANCER_IP}:{LOAD_BALANCER_PORT}"
    subprocess.Popen([sys.executable, 'InsultFilter/InsultFilterServer.py', insult_url, str(port)])
    return FilterNode(port)

# Initialize nodes based on the selected mode
def initialize_nodes():
    for i in range(NUM_OF_NODES):
        spawn_insult_node()
        #spawn_filter_node()

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
    if len(_InsultNodeList) > 1:
        _RR_insult_index = (_RR_insult_index + 1) % len(_InsultNodeList)
    return node

# Round-robin or static selection for filter nodes
def get_filter_node():
    global _RR_filter_index
    node = _FilterNodeList[_RR_filter_index]
    if len(_FilterNodeList) > 1:
        _RR_filter_index = (_RR_filter_index + 1) % len(_FilterNodeList)
    return node

# Fill the server with insults for the test
def fillServerWithInsults(url):
    insults = ["clown", "blockhead", "dimwit", "nincompoop", "simpleton", "dullard", "buffoon", "nitwit", "half-wit", "scatterbrain", "scatterbrained", "knucklehead", "dingbat", "doofus", "ninny", "ignoramus", "muttonhead", "bonehead", "airhead", "puddingbrain", "mushbrain", "blockhead", "dunderhead", "lamebrain", "muttonhead", "numbskull", "dimwit", "dullard", "fool", "goofball", "knucklehead", "lunkhead", "maroon", "mook", "nincompoop", "ninnyhammer", "numskull", "patzer", "puddingbrain", "sap", "simpleton", "scofflaw", "screwball", "twit", "woozle", "yahoo", "zany"]
    server = ServerProxy(url, allow_none=True)
    for ins in insults:
        server.add(ins)

def floadServer(url):
    victim = ServerProxy(url, allow_none=True)
    for _ in range(REQS_PER_WORKER):
        victim.insult()

def spawnWorkers(ports, num):
    for port in ports:
        dir = f'http://127.0.0.1:{port}'
        for _ in range(num):
            p = mp.Process(target=floadServer, args=(dir,))
            _workers.append(p)
            p.start()

def waitForWorkers():
    for w in _workers:
        w.join()

if __name__=='__main__':
    # Start initial nodes
    print("Spawning all the nodes...")
    initialize_nodes()
    time.sleep(2)

    print("Filling the servers with insults...")
    for node in _InsultNodeList: fillServerWithInsults(f'http://127.0.0.1:{node.port}')

    print("Starting test... (making every worker do ", REQS_PER_WORKER, " reqs)")
    listOfPorts = []
    for node in _InsultNodeList: listOfPorts.append(node.port)
    delta = time.time()
    spawnWorkers(listOfPorts, NUM_OF_WORKERS)
    waitForWorkers()
    delta = time.time() - delta

    print("Test finished.")
    reqs = len(listOfPorts)*NUM_OF_WORKERS*REQS_PER_WORKER
    print("RES: Made ", reqs, " reqs in ", delta, " secs. Got ", (reqs/delta), " reqs/s")