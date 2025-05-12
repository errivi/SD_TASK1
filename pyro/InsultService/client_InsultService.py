import time
import random
import multiprocessing
import Pyro4

_workers = []
_NUM_GOBLINS = 1

# URI format: PYRO:insultService@hostname:port
BASE_URI = "PYRO:insultService@localhost:7999"

insults = [
    "clown", "blockhead", "dimwit", "nincompoop", "simpleton",
    "dullard", "buffoon", "nitwit", "half-wit", "scatterbrain",
    "scatterbrained", "knucklehead", "dingbat", "doofus", "ninny",
    "ignoramus", "muttonhead", "bonehead", "airhead", "puddingbrain",
    "mushbrain", "dunderhead", "lamebrain", "numbskull", "fool",
    "goofball", "lunkhead", "maroon", "mook", "ninnyhammer",
    "numskull", "patzer", "sap", "scofflaw", "screwball",
    "twit", "woozle", "yahoo", "zany"
]

@Pyro4.expose
class LoadTester:
    def __init__(self, uri, goblin_id):
        self.victim = Pyro4.Proxy(uri)
        self.goblin_id = goblin_id

    def run(self):
        while True:
            op = random.choice(["add", "get", "insult"])
            start = time.time()
            if op == "add":
                self.victim.add(random.choice(insults))
            elif op == "get":
                self.victim.get()
            else:
                self.victim.insult()
            latency = time.time() - start
            print(f"[Goblin {self.goblin_id}] {op} took {latency:.4f}s")


def spawn_goblins():
    for i in range(_NUM_GOBLINS):
        tester = LoadTester(BASE_URI, i)
        p = multiprocessing.Process(target=tester.run)
        _workers.append(p)
        p.start()


def kill_goblins():
    for p in _workers:
        if p.is_alive():
            p.terminate()


def fload_server(duration=3):
    spawn_goblins()
    time.sleep(duration)
    kill_goblins()


if __name__ == '__main__':
    # Inicia el Name Server si lo necesitas:
    # Pyro4.naming.startNSloop()
    fload_server()
