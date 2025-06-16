from xmlrpc.client import ServerProxy
import subprocess
import sys
import time
import multiprocessing as mp
import random

NUM_OF_NODES = int(sys.argv[1]) if len(sys.argv) > 1 and int(sys.argv[1]) > 0 else 0

LOAD_BALANCER_PORT = 7999
LOAD_BALANCER_IP = "127.0.0.1"
BASE_SERVER_HOST = "127.0.0.1"
BASE_INSULT_SERVER_PORT = 8000
BASE_FILTER_SERVER_PORT = 9000

# Global lists of nodes
_InsultNodeList = []
_FilterNodeList = []

_clients = []
_servers = []

# Test configurations
TOTAL_NUM_REQS = 10_000
NUM_OF_CLIENTS = 6
REQS_PER_CLIENT = int(TOTAL_NUM_REQS / (NUM_OF_CLIENTS))

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
    s = subprocess.Popen([sys.executable, 'InsultService/InsultServer.py', str(port)])
    _servers.append(s)
    return InsultNode(port)

# Spawn a filter node linked to a specific insult node
def spawn_filter_node(): 
    port = BASE_FILTER_SERVER_PORT + len(_FilterNodeList)
    insult_url = f"http://{BASE_SERVER_HOST}:{BASE_INSULT_SERVER_PORT}"
    s = subprocess.Popen([sys.executable, 'InsultFilter/InsultFilterServer.py', insult_url, str(port)])
    _servers.append(s)
    return FilterNode(port)

# Fill the server with insults for the test
def fillServerWithInsults(url):
    insults = ["clown", "blockhead", "dimwit", "nincompoop", "simpleton", "dullard", "buffoon", "nitwit", "half-wit", "scatterbrain", "scatterbrained", "knucklehead", "dingbat", "doofus", "ninny", "ignoramus", "muttonhead", "bonehead", "airhead", "puddingbrain", "mushbrain", "blockhead", "dunderhead", "lamebrain", "muttonhead", "numbskull", "dimwit", "dullard", "fool", "goofball", "knucklehead", "lunkhead", "maroon", "mook", "nincompoop", "ninnyhammer", "numskull", "patzer", "puddingbrain", "sap", "simpleton", "scofflaw", "screwball", "twit", "woozle", "yahoo", "zany"]
    server = ServerProxy(url, allow_none=True)
    for ins in insults:
        server.add(ins)

def floadFilterServer(url):
    phrases = ["You absolute buffoon, always acting like a total clown and making everyone around you cringe with your dimwit antics, you complete nincompoop who can't even tie his own shoelaces.",
            "Honestly, you're such a dullard and a nitwit that it's amazing you manage to breathe without causing some sort of catastrophe, you half-witted scatterbrain with the intelligence of a turnip.",
            "Listening to your stupidity is like hearing a bunch of buffoons trying to solve a simple problem, you knuckleheaded doofus who never learns from their idiotic mistakes, you utter ninny.",
            "You dimwit, you clueless nincompoop, your brain is so mushy and pudding-like that I wonder how you even function in everyday life, you scatterbrained fool with no common sense at all.",
            "You absolute simpleton, always acting like a total moron and never catching on to anything, you nitwit of a bonehead who seems to exist solely to embarrass himself with every word he speaks.",
            "You complete blockhead, always stumbling through life like a buffoon and proving time and again that you're nothing more than a dullard with the mental capacity of a lizard, you utter nincompoop.",
            "Honestly, you’re such a scatterbrained dimwit and a total ninnyhammer that I wouldn’t trust you to pour water out of a boot even if the instructions were on the heel, you doofus.",
            "Your mind is a total mushbrain, you clueless nincompoop, and your inability to understand simple things makes you the perfect example of a bonehead and a half-wit combined, you ignoramus.",
            "Listening to your nonsense is like hearing a bunch of fools trying to solve a puzzle with half the pieces missing, you knuckleheaded nitwit who’s always a step behind everyone else, you maroon.",
            "You are a hopeless simpleton and a true scatterbrained fool, a dullard who manages to bungle basic tasks and make a fool of himself every time you open your mouth, you ninnyhammer.",
            "Pardon my intromission, gentleman, but I must request you to empty the compartments of your pantaloons."
    ]
    victims = [ServerProxy(uri, allow_none=True) for uri in url]
    RR_uris = 0
    maxURIs = len(victims)
    for _ in range(REQS_PER_CLIENT):
        victims[RR_uris].filter(random.choice(phrases))
        RR_uris = RR_uris + 1
        if (RR_uris == maxURIs): RR_uris = 0

def floadInsultServer(url):
    victims = [ServerProxy(uri, allow_none=True) for uri in url]
    RR_uris = 0
    maxURIs = len(victims)
    for _ in range(REQS_PER_CLIENT):
        victims[RR_uris].insult()
        RR_uris = RR_uris + 1
        if (RR_uris == maxURIs): RR_uris = 0

def spawnClients(ports, num, work):
    for _ in range(num):
        p = mp.Process(target=work, args=(ports,))
        _clients.append(p)
        p.start()

def waitForClients():
    for w in _clients:
        w.join()

def callProfile():
    # Start initial service nodes
    print("Spawning all the nodes...")
    for _ in range(NUM_OF_NODES): spawn_insult_node()
    time.sleep(2)
    serversURIs = []
    for node in _InsultNodeList: serversURIs.append(f'http://127.0.0.1:{node.port}')

    # Testing InsultService
    print("Filling the servers with insults...")
    for uri in serversURIs: fillServerWithInsults(uri)

    for _ in range(NUM_OF_NODES): spawn_filter_node()
    time.sleep(2)

    print("Servers ready for testing, press any key to close the servers...")
    input()
    time.sleep(1)

    victims = [ServerProxy(uri, allow_none=True) for uri in serversURIs]
    baseCase = [time.perf_counter for _ in serversURIs]
    RR_uris = 0
    maxURIs = len(victims)
    bS, aS, bM, aM, bC, aC, BbS, BaS, BbC, BaC = 0,0,0,0,0,0,0,0,0,0
    aux = None
    res = None
    for iter in range(5):
        bS = time.perf_counter_ns()
        aux = victims[RR_uris]
        aS = time.perf_counter_ns()
        bM = time.perf_counter_ns()
        aux = aux.insult
        aM = time.perf_counter_ns()
        bC = time.perf_counter_ns()
        res = aux()
        aC = time.perf_counter_ns()
        
        BbS = time.perf_counter_ns()
        aux = baseCase[RR_uris]
        BaS = time.perf_counter_ns()
        BbC = time.perf_counter_ns()
        res = aux()
        BaC = time.perf_counter_ns()
    
        print(f"Iter {iter} with {maxURIs} servers:\n\tReal -> aS-bS: {aS-bS}, aM-bM: {aM-bM}, aC-bC: {aC-bC}\n\tBase -> aS-bS: {BaS-BbS}, aC-bC: {BaC-BbC}\n")
    
        RR_uris = RR_uris + 1
        if (RR_uris == maxURIs): RR_uris = 0

    # Kill everything
    print("Stopping all nodes...")
    for thread in _clients: thread.kill()
    for server in _servers: server.kill()
    sys.exit(0)

def test():
    # Start initial service nodes
    print("Spawning all the nodes...")
    for _ in range(NUM_OF_NODES): spawn_insult_node()
    time.sleep(2)
    serversURIs = []
    for node in _InsultNodeList: serversURIs.append(f'http://127.0.0.1:{node.port}')

    # Testing InsultService
    print("Filling the servers with insults...")
    for uri in serversURIs: fillServerWithInsults(uri)

    print("Starting Insult test... (making every client do ", REQS_PER_CLIENT, " reqs)")

    delta = time.time()
    spawnClients(ports=serversURIs, num=NUM_OF_CLIENTS, work=floadInsultServer)
    waitForClients()
    delta = time.time() - delta

    print("Test finished.")
    reqs = NUM_OF_CLIENTS*REQS_PER_CLIENT
    print("RES: Made ", reqs, " reqs in ", delta, " secs. Got ", (reqs/delta), " reqs/s")

    # Spawning initial filter nodes
    for _ in range(NUM_OF_NODES): spawn_filter_node()
    time.sleep(2)

    # Testing InsultFilter
    print("Starting Filter test... (making every client do ", REQS_PER_CLIENT, " reqs)")
    serversURIs = []
    for node in _FilterNodeList: serversURIs.append(f'http://127.0.0.1:{node.port}')

    delta = time.time()
    spawnClients(ports=serversURIs, num=NUM_OF_CLIENTS, work=floadFilterServer)
    waitForClients()
    delta = time.time() - delta

    print("Test finished.")
    reqs = NUM_OF_CLIENTS*REQS_PER_CLIENT
    print("RES: Made ", reqs, " reqs in ", delta, " secs. Got ", (reqs/delta), " reqs/s")

    # Kill everything
    print("Stopping all nodes...")
    for thread in _clients: thread.kill()
    for server in _servers: server.kill()
    sys.exit(0)

if __name__=='__main__':
    test()