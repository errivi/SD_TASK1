import time
import random
import multiprocessing
import threading
import redis

# Configuration
REDIS_HOST = 'localhost'
REDIS_PORT = 6379
INSULTS_SET_KEY = 'insults'
PUBSUB_CHANNEL = 'insults_channel'
_NUM_WORKERS = 1

insults_list = [
    "clown", "blockhead", "dimwit", "nincompoop", "simpleton",
    "dullard", "buffoon", "nitwit", "half-wit", "scatterbrain",
    "scatterbrained", "knucklehead", "dingbat", "doofus", "ninny",
    "ignoramus", "muttonhead", "bonehead", "airhead", "puddingbrain",
    "mushbrain", "dunderhead", "lamebrain", "numbskull", "fool",
    "goofball", "lunkhead", "maroon", "mook", "ninnyhammer",
    "numskull", "patzer", "sap", "scofflaw", "screwball",
    "twit", "woozle", "yahoo", "zany"
]

class Worker:
    def __init__(self, worker_id):
        self.r = redis.Redis(host=REDIS_HOST, port=REDIS_PORT, decode_responses=True)
        self.worker_id = worker_id
        self.pubsub = self.r.pubsub()
        self.pubsub.subscribe(PUBSUB_CHANNEL)

    def listen(self):
        for message in self.pubsub.listen():
            if message['type'] == 'message':
                print(f"[Worker {self.worker_id}] Received insult: {message['data']}")

    def run(self):
        # Start listener thread
        threading.Thread(target=self.listen, daemon=True).start()
        # Issue random operations in loop
        while True:
            op = random.choice(['add', 'get', 'random'])
            start = time.time()
            if op == 'add':
                insult = random.choice(insults_list)
                self.r.sadd(INSULTS_SET_KEY, insult)
            elif op == 'get':
                _ = self.r.smembers(INSULTS_SET_KEY)
            else:
                insults = list(self.r.smembers(INSULTS_SET_KEY))
                _ = random.choice(insults) if insults else None
            latency = time.time() - start
            print(f"[Worker {self.worker_id}] {op} took {latency:.4f}s")
            time.sleep(1)


def spawn_workers():
    procs = []
    for i in range(_NUM_WORKERS):
        p = multiprocessing.Process(target=Worker(i).run)
        procs.append(p)
        p.start()
    return procs

def kill_workers(procs):
    for p in procs:
        if p.is_alive():
            p.terminate()

if __name__ == '__main__':
    try:
        procs = spawn_workers()
        time.sleep(10)  # run for 10 seconds
    finally:
        kill_workers(procs)