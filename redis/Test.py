import redis
import json
import time
import sys
import multiprocessing
import subprocess

# Configuration
REDIS_HOST = 'localhost'
REDIS_PORT = 6379
COMMAND_QUEUE = 'insult_channel'
RESPONSE_QUEUE = 'insult_response_queue'
NUM_REQUESTS = 10_000
CLIENTS = 10

# Parse number of nodes from command-line
num_nodes = int(sys.argv[1]) if len(sys.argv) > 1 and sys.argv[1].isdigit() else 1
# Requests per client
reqs_per_client = NUM_REQUESTS // CLIENTS

_servers = []

class RedisInsultClient:
    def __init__(self, host=REDIS_HOST, port=REDIS_PORT):
        self.r = redis.Redis(host=host, port=port, decode_responses=True)

    def insult_me(self):
        cmd = json.dumps({'method': 'insult', 'arg': None})
        self.r.lpush(COMMAND_QUEUE, cmd)
        _, raw = self.r.brpop(RESPONSE_QUEUE)
        return json.loads(raw).get('insult')


def client_task(start_event):
    client = RedisInsultClient()
    # wait until main process signals start
    start_event.wait()
    for _ in range(reqs_per_client):
        client.insult_me()

if __name__ == '__main__':
    print(f"Launching {num_nodes} InsultServer nodes...")
    for _ in range(num_nodes):
        _servers.append(subprocess.Popen([sys.executable, 'InsultService/InsultServer.py']))
    time.sleep(3)

    # Use multiprocessing Event to sync start across processes
    start_event = multiprocessing.Event()
    processes = [multiprocessing.Process(target=client_task, args=(start_event,))
                 for _ in range(CLIENTS)]

    print(f"Launching {CLIENTS} client processes, each sending {reqs_per_client} requests ({CLIENTS * reqs_per_client} total)")

    # Start all client processes
    for p in processes:
        p.start()

    # Warm-up: single request to initialize server connections
    RedisInsultClient().insult_me()

    # Begin timing
    t0 = time.perf_counter()
    start_event.set()  # signal all clients to start

    # Wait for all processes to finish
    for p in processes:
        p.join()

    t1 = time.perf_counter()
    total_time = t1 - t0
    requests_per_second = (CLIENTS * reqs_per_client) / total_time


    print(f"Executed {CLIENTS * reqs_per_client} requests in {total_time:.2f} seconds")
    print(f"Requests per second: {requests_per_second:.2f} req/s")
    
    print(f"Stoping all the servers...")
    for p in _servers: p.kill()