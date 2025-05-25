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

_workers = []
_servers = []

# Test configurations
TOTAL_NUM_REQS = 150_000
NUM_OF_WORKERS = 4
REQS_PER_WORKER = int(TOTAL_NUM_REQS / (NUM_OF_WORKERS))

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
    for _ in range(REQS_PER_WORKER):
        victims[RR_uris].filter(random.choice(phrases))
        RR_uris = RR_uris + 1
        if (RR_uris == maxURIs): RR_uris = 0

def floadInsultServer(url):
    victims = [ServerProxy(uri, allow_none=True) for uri in url]
    RR_uris = 0
    maxURIs = len(victims)
    for _ in range(REQS_PER_WORKER):
        victims[RR_uris].insult()
        RR_uris = RR_uris + 1
        if (RR_uris == maxURIs): RR_uris = 0

def spawnWorkers(ports, num, work):
    for _ in range(num):
        p = mp.Process(target=work, args=(ports,))
        _workers.append(p)
        p.start()

def waitForWorkers():
    for w in _workers:
        w.join()

if __name__=='__main__':
    # Start initial service nodes
    print("Spawning all the nodes...")
    for _ in range(NUM_OF_NODES): spawn_insult_node()
    time.sleep(2)
    serversURIs = []
    for node in _InsultNodeList: serversURIs.append(f'http://127.0.0.1:{node.port}')

    # Testing InsultService
    print("Filling the servers with insults...")
    for uri in serversURIs: fillServerWithInsults(uri)

    print("Starting Insult test... (making every worker do ", REQS_PER_WORKER, " reqs)")

    delta = time.time()
    spawnWorkers(ports=serversURIs, num=NUM_OF_WORKERS, work=floadInsultServer)
    waitForWorkers()
    delta = time.time() - delta

    print("Test finished.")
    reqs = NUM_OF_NODES*NUM_OF_WORKERS*REQS_PER_WORKER
    print("RES: Made ", reqs, " reqs in ", delta, " secs. Got ", (reqs/delta), " reqs/s")

    # Spawning initial filter nodes
    for _ in range(NUM_OF_NODES): spawn_filter_node()
    time.sleep(2)

    # Testing InsultFilter
    print("Starting Filter test... (making every worker do ", REQS_PER_WORKER, " reqs)")
    serversURIs = []
    for node in _FilterNodeList: serversURIs.append(f'http://127.0.0.1:{node.port}')

    delta = time.time()
    spawnWorkers(ports=serversURIs, num=NUM_OF_WORKERS, work=floadFilterServer)
    waitForWorkers()
    delta = time.time() - delta

    print("Test finished.")
    reqs = NUM_OF_NODES*NUM_OF_WORKERS*REQS_PER_WORKER
    print("RES: Made ", reqs, " reqs in ", delta, " secs. Got ", (reqs/delta), " reqs/s")

    # Kill everything
    print("Stopping all nodes...")
    for thread in _workers: thread.kill()
    for server in _servers: server.kill()
    sys.exit(0)