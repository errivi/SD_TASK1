import sys
import subprocess
import time
import random
import multiprocessing as mp
import Pyro4

NUM_OF_NODES = int(sys.argv[1]) if len(sys.argv) > 1 and int(sys.argv[1]) > 1 else 1

LOAD_BALANCER_NS = "PYRONAME:LoadBalancer"
BASE_HOST = "127.0.0.1"
BASE_INSULT_SERVER_PORT = 8000
BASE_FILTER_SERVER_PORT = 9000

# Global lists of nodes
_InsultNodeList = []
_FilterNodeList = []

_clients = []

# Test configurations
TOTAL_REQS = 10_000
NUM_CLIENTS = 10
REQS_PER_CLIENT = int(TOTAL_REQS // (NUM_OF_NODES * NUM_CLIENTS))

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
    subprocess.Popen([sys.executable,'InsultService/InsultServer.py',str(port)])
    return InsultNode(port)

# Spawn a filter node linked to a specific insult node
def spawn_filter_node():
    port = BASE_FILTER_SERVER_PORT + len(_FilterNodeList)
    insult_uri = f"PYRO:example.InsultServer@{BASE_HOST}:{BASE_INSULT_SERVER_PORT}"
    subprocess.Popen([sys.executable,'InsultFilter/InsultFilterServer.py',insult_uri,str(port)])
    return FilterNode(port)

# Fill the server with insults for the test
def fillServerWithInsults(uri):
    insults = ["clown", "blockhead", "dimwit", "nincompoop", "simpleton", "dullard", "buffoon", "nitwit", "half-wit", "scatterbrain", "scatterbrained", "knucklehead", "dingbat", "doofus", "ninny", "ignoramus", "muttonhead", "bonehead", "airhead", "puddingbrain", "mushbrain", "blockhead", "dunderhead", "lamebrain", "muttonhead", "numbskull", "dimwit", "dullard", "fool", "goofball", "knucklehead", "lunkhead", "maroon", "mook", "nincompoop", "ninnyhammer", "numskull", "patzer", "puddingbrain", "sap", "simpleton", "scofflaw", "screwball", "twit", "woozle", "yahoo", "zany"]
    proxy = Pyro4.Proxy(uri)
    for ins in insults:
        proxy.add_insult(ins)

# Stress test for InsultServer
def floadInsultServer(uri):
    proxy = Pyro4.Proxy(uri)
    for _ in range(REQS_PER_CLIENT):
        proxy.insult_me()

# Stress test for FilterServer
def floadFilterServer(uri):
    proxy = Pyro4.Proxy(uri)
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
    for _ in range(REQS_PER_CLIENT):
        proxy.filter_text(random.choice(phrases))

# Spawn clients passing the function, not calling it
def spawnClients(ports, func):
    for port in ports:
        # Determine URI depending function
        if func is floadInsultServer:
            uri = f"PYRO:example.InsultServer@{BASE_HOST}:{port}"
        else:
            uri = f"PYRO:example.InsultFilterServer@{BASE_HOST}:{port}"
        for _ in range(NUM_CLIENTS):
            p = mp.Process(target=func, args=(uri,))
            _clients.append(p)
            p.start()

# Wait for all clients
def waitForClients():
    for p in _clients:
        p.join()

if __name__ == '__main__':
    # Start initial service nodes
    print("Spawning all the nodes...")
    for _ in range(NUM_OF_NODES): spawn_insult_node()
    time.sleep(2)

    # Testing InsultService
    print("Filling the servers with insults...")
    for node in _InsultNodeList:
        uri = f"PYRO:example.InsultServer@{BASE_HOST}:{node.port}"
        fillServerWithInsults(uri)

    print("Starting Insult test... (making every client do ", REQS_PER_CLIENT, " reqs)")
    listOfPorts = []
    for node in _InsultNodeList: listOfPorts.append(node.port)

    delta = time.time()
    spawnClients(listOfPorts, floadInsultServer)
    waitForClients()
    delta = time.time() - delta

    print("Test finished.")
    reqs = len(listOfPorts) * NUM_CLIENTS * REQS_PER_CLIENT
    print("RES: Made ", reqs, " reqs in ", delta, " secs. Got ", (reqs/delta), " reqs/s")

    # Spawning initial filter nodes
    for _ in range(NUM_OF_NODES): spawn_filter_node()
    time.sleep(2)

    # Testing InsultFilter
    print("Starting Filter test... (making every client do ", REQS_PER_CLIENT, " reqs)")
    listOfPorts = []
    for node in _FilterNodeList: listOfPorts.append(node.port)

    delta = time.time()
    spawnClients(listOfPorts, floadFilterServer)
    waitForClients()
    delta = time.time() - delta

    print("Test finished.")
    reqs = len(listOfPorts) * NUM_CLIENTS * REQS_PER_CLIENT
    print("RES: Made ", reqs, " reqs in ", delta, " secs. Got ", (reqs/delta), " reqs/s")

    # Kill everything
    print("Stopping all nodes...")
    for p in _clients:
        p.terminate()
    sys.exit(0)
