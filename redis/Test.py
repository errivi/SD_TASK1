import sys
import subprocess
import time
import random
import multiprocessing as mp
import redis

# Configuración de nodos\ nNUM_OF_NODES = int(sys.argv[1]) if len(sys.argv) > 1 and int(sys.argv[1]) > 1 else 1
BASE_HOST = '127.0.0.1'
BASE_INSULT_PORT = 8000
BASE_FILTER_PORT = 9000

# Redis\ nREDIS_HOST = 'localhost'
REDIS_PORT = 6379
PUBSUB_CHANNEL = 'insults_channel'
FILTERED_LIST_KEY = 'filtered_texts'

# Carga\ nTOTAL_REQS = 200_000
NUM_WORKERS = 8
REQS_PER_WORKER = TOTAL_REQS // (NUM_OF_NODES * NUM_WORKERS)
_workers = []

class InsultNode:
    def __init__(self, port):
        self.port = port

class FilterNode:
    def __init__(self, port):
        self.port = port

# Arranca procesos server de insult
    def spawn_insult_node():
    port = BASE_INSULT_PORT + len(insult_nodes)
    subprocess.Popen([sys.executable, 'InsultService/InsultServer.py', str(port)])
    insult_nodes.append(InsultNode(port))

# Arranca procesos server filter
 def spawn_filter_node():
    port = BASE_FILTER_PORT + len(filter_nodes)
    subprocess.Popen([sys.executable, 'InsultFilter/InsultFilterServer.py', str(port)])
    filter_nodes.append(FilterNode(port))

# Worker de publish/subscripció
 def floadInsultServer(_):
    r = redis.Redis(host=REDIS_HOST, port=REDIS_PORT, decode_responses=True)
    for _ in range(REQS_PER_WORKER):
        insult = random.choice(list(r.smembers('insults')))
        r.publish(PUBSUB_CHANNEL, insult)

# Worker de filter
 def floadFilterServer(_):
    r = redis.Redis(host=REDIS_HOST, port=REDIS_PORT, decode_responses=True)
    phrase = random.choice(["some text with clown", "another with blockhead"])
    r.rpush(FILTERED_LIST_KEY, re.sub(r"clown|blockhead", 'CENSORED', phrase))

# Spawn workers
 def spawn_workers(func):
    for _ in range(NUM_WORKERS * NUM_OF_NODES):
        p = mp.Process(target=func, args=(None,))
        _workers.append(p)
        p.start()

# Espera
 def wait_workers():
    for p in _workers: p.join()

if __name__ == '__main__':
    insult_nodes = []
    filter_nodes = []
    for _ in range(NUM_OF_NODES):
        spawn_insult_node()
        spawn_filter_node()
    time.sleep(2)

    # Test Insult
    spawn_workers(floadInsultServer)
    wait_workers()

    # Test Filter
    spawn_workers(floadFilterServer)
    wait_workers()

    print('Done')
