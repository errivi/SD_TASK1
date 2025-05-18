import time
import random
import multiprocessing
import redis

_workers = []
_NUM_GOBLINS = 1

# Redis configuration
REDIS_HOST = 'localhost'
REDIS_PORT = 6379
INSULTS_SET_KEY = 'insults'

# Redis client
r = redis.Redis(host=REDIS_HOST, port=REDIS_PORT, decode_responses=True)

# Same insults list
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

class LoadTester:
    def __init__(self, goblin_id):
        self.goblin_id = goblin_id

    def run(self):
        while True:
            op = random.choice(["add", "get", "insult"])
            start = time.time()
            if op == "add":
                r.sadd(INSULTS_SET_KEY, random.choice(insults))
            elif op == "get":
                r.smembers(INSULTS_SET_KEY)
            else:
                # random member from set or "NoInsultsSaved"
                count = r.scard(INSULTS_SET_KEY)
                if count == 0:
                    _ = "NoInsultsSaved"
                else:
                    _ = r.srandmember(INSULTS_SET_KEY)
            latency = time.time() - start
            print(f"[Goblin {self.goblin_id}] {op} took {latency:.4f}s")


def spawn_goblins():
    for i in range(_NUM_GOBLINS):
        tester = LoadTester(i)
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
    fload_server()
