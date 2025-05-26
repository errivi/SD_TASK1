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
_RR_insult_index = 0
_RR_filter_index = 0

_workers = []

# Test configurations
TOTAL_REQS = 9000
NUM_WORKERS = 6
REQS_PER_WORKER = int(TOTAL_REQS // (NUM_OF_NODES * NUM_WORKERS))

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
def fillServerWithInsults(uri):
    insults = ["clown", "blockhead", "dimwit", "nincompoop", "simpleton", "dullard", "buffoon", "nitwit", "half-wit", "scatterbrain", "scatterbrained", "knucklehead", "dingbat", "doofus", "ninny", "ignoramus", "muttonhead", "bonehead", "airhead", "puddingbrain", "mushbrain", "blockhead", "dunderhead", "lamebrain", "muttonhead", "numbskull", "dimwit", "dullard", "fool", "goofball", "knucklehead", "lunkhead", "maroon", "mook", "nincompoop", "ninnyhammer", "numskull", "patzer", "puddingbrain", "sap", "simpleton", "scofflaw", "screwball", "twit", "woozle", "yahoo", "zany"]
    proxy = Pyro4.Proxy(uri)
    for ins in insults:
        proxy.add_insult(ins)

# Stress test for InsultServer
def floadInsultServer(uri):
    proxy = Pyro4.Proxy(uri)
    for _ in range(REQS_PER_WORKER):
        proxy.insult_me()

# Stress test for FilterServer
def floadFilterServer(uri):
    proxy = Pyro4.Proxy(uri)
    phrases = [
        "You're such a clown, always acting the fool.",
        "Honestly, you're a blockhead who can't catch a break.",
        "That idea was as dimwitted as it gets.",
        "Stop being a nincompoop and think for a second.",
        "You're a simpleton with no sense of the bigger picture.",
        "Dullard, your ignorance is astonishing.",
        "Don't be a buffoon; it's embarrassing.",
        "What a nitwit move you just pulled.",
        "Half-wit decisions lead to half-witted results.",
        "You're a scatterbrain, always forgetting something important.",
        "His scatterbrained antics are getting old.",
        "Knucklehead, you nearly caused a disaster.",
        "Dingbat, can't you see how silly that is?",
        "You're such a doofus sometimes, it's hilarious.",
        "Ninny, do you even think before speaking?",
        "You ignoramus, do you even listen?",
        "Muttonhead, get your facts straight.",
        "Bonehead move there, genius.",
        "Airhead alert: did you forget everything?",
        "Puddingbrain, your ideas are pudding for brains.",
        "Mushbrain, you're all over the place.",
        "Blockhead, you missed the obvious again.",
        "Dunderhead, it's not that complicated.",
        "Lamebrain, try using that thing between your ears.",
        "Numbskull, you really outdid yourself this time.",
        "Fool, thinking that would work.",
        "Goofball, lighten up a bit.",
        "Lunkhead, don't hurt yourself trying to think.",
        "Maroon, you really went the extra mile in stupidity.",
        "Mook, you're not fooling anyone.",
        "Nincompoop strikes again!",
        "Ninnyhammer, what a charming display of ignorance.",
        "Numskull, your brain is on vacation.",
        "Patzer, get your act together.",
        "Sap, your words lack any sense.",
        "Simpleton, it's not that hard to understand.",
        "Screwball ideas from a real screw-up.",
        "Twit, you really outdid yourself today.",
        "Woozle, I didn't expect that from you.",
        "Yahoo! Someone's feeling adventurous today.",
        "Honestly, your level of stupidity is so impressive that I sometimes wonder if you're doing it on purpose.",
        "You're the kind of person who could trip over a cordless phone and still manage to blame everyone else.",
        "If there was a contest for being a blockhead, you'd be the reigning champion, no doubt about it.",
        "Your ideas are so dimwitted, they could light up a small city if only they made any sense.",
        "It's remarkable how you manage to be both scatterbrained and stubborn at the same time.",
        "You have the intellect of a doofus who just discovered how to tie their shoes for the first time.",
        "You're such a nincompoop that even a goldfish would be embarrassed to be associated with your forgetfulness.",
        "Your decision-making skills are so lacking, I wouldn't trust you to pick a paperclip, let alone run a business.",
        "Honestly, trying to have a serious conversation with you is like talking to a dingbat who refuses to listen.",
        "You're the perfect example of a dullard who thinks they're smarter than everyone else, which is adorable and tragic at the same time.",
        "If ignorance is bliss, then you must be the happiest person alive, because you seem to have no idea what's going on.",
        "Your antics are so buffoonish that I wonder if you were born without a brain or just chose to ignore it.",
        "It's astonishing how a nitwit like you manages to stumble through life without tripping over your own stupidity.",
        "You must be a true scatterbrain because you forget everything, including your own name sometimes.",
        "Honestly, you're such a knucklehead that I wouldn't be surprised if you thought a microwave was a type of spaceship.",
        "You do realize that calling yourself a fool repeatedly doesn't make you wise, right?",
        "Your doofus tendencies are so evident that even a blind person would see right through them.",
        "You're a ninny, and it's almost impressive how you manage to function with such limited insight.",
        "It's sad how ignoramus you are, yet you walk around acting like you're the smartest person in the room.",
        "You're a muttonhead who thinks that more stupidity equals more fun, but it just makes you look foolish.",
        "Your boneheaded decisions are legendary, even among the most clueless individuals.",
        "You’re such an airhead that I’m surprised you don’t float away with all your nonsense.",
        "Puddingbrain, your thoughts are as soft and flavorless as a bowl of pudding.",
        "Mushbrain, your ideas are so muddled that they defy any logic or sense.",
        "Blockhead, you’ve managed to turn a simple task into a comedy of errors.",
        "Dunderhead, you must have been born without a clue or just decided to ignore it altogether.",
        "Lamebrain, your inability to think straight is truly a gift to us all.",
        "Numbskull, you’ve got the intelligence of a rock and the charm of a damp sponge.",
        "Fool, you keep proving that common sense isn’t so common after all.",
        "Goofball, your antics are so ridiculous that they could be turned into a comedy show.",
        "Lunkhead, your lack of insight is matched only by your overconfidence.",
        "Maroon, you’ve painted yourself into a corner with your own stupidity.",
        "Mook, you’re walking proof that some people are born to be clueless.",
        "Nincompoop, your ideas are so out there, they border on the absurd.",
        "Ninnyhammer, your ignorance is a shining example for future generations.",
        "Numskull, your brain must be on permanent vacation because it sure isn’t working now.",
        "Patzer, your poor judgment is matched only by your lack of common sense.",
        "Sap, your words are as empty as your head is full of air.",
        "Simpleton, it’s amazing how you manage to make everything more complicated than it needs to be.",
        "Screwball, your logic is so twisted it could give a pretzel a run for its money.",
        "Twit, you’re so clueless that I wouldn’t trust you to carry a bucket of water without spilling it.",
        "Woozle, your confusion is so profound that even Winnie the Pooh would be baffled.",
        "Yahoo! Looks like someone’s having a wild day, but probably not in the good way.",
        "Zany times with you—though mostly just bizarre and confusing.",
        "Zany as always, but not in a good way.",
    ]
    for _ in range(REQS_PER_WORKER):
        proxy.filter_text(random.choice(phrases))

# Spawn workers passing the function, not calling it
def spawnWorkers(ports, func):
    for port in ports:
        # Determine URI depending function
        if func is floadInsultServer:
            uri = f"PYRO:example.InsultServer@{BASE_HOST}:{port}"
        else:
            uri = f"PYRO:example.InsultFilterServer@{BASE_HOST}:{port}"
        for _ in range(NUM_WORKERS):
            p = mp.Process(target=func, args=(uri,))
            _workers.append(p)
            p.start()

# Wait for all workers
def waitForWorkers():
    for p in _workers:
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

    print("Starting Insult test... (making every worker do ", REQS_PER_WORKER, " reqs)")
    listOfPorts = []
    for node in _InsultNodeList: listOfPorts.append(node.port)

    delta = time.time()
    spawnWorkers(listOfPorts, floadInsultServer)
    waitForWorkers()
    delta = time.time() - delta

    print("Test finished.")
    reqs = len(listOfPorts) * NUM_WORKERS * REQS_PER_WORKER
    print("RES: Made ", reqs, " reqs in ", delta, " secs. Got ", (reqs/delta), " reqs/s")

    # Spawning initial filter nodes
    for _ in range(NUM_OF_NODES): spawn_filter_node()
    time.sleep(2)

    # Testing InsultFilter
    print("Starting Filter test... (making every worker do ", REQS_PER_WORKER, " reqs)")
    listOfPorts = []
    for node in _FilterNodeList: listOfPorts.append(node.port)

    delta = time.time()
    spawnWorkers(listOfPorts, floadFilterServer)
    waitForWorkers()
    delta = time.time() - delta

    print("Test finished.")
    reqs = len(listOfPorts) * NUM_WORKERS * REQS_PER_WORKER
    print("RES: Made ", reqs, " reqs in ", delta, " secs. Got ", (reqs/delta), " reqs/s")

    # Kill everything
    print("Stopping all nodes...")
    for p in _workers:
        p.terminate()
    sys.exit(0)
