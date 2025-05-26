# stress_test_client.py
#!/usr/bin/env python3
import redis
import json
import time
import sys
import multiprocessing

# Configuration
REDIS_HOST = 'localhost'
REDIS_PORT = 6379
COMMAND_QUEUE = 'insult_channel'
RESPONSE_QUEUE = 'insult_response_queue'
NUM_REQUESTS = 9_000
WORKERS_PER_NODE = 8

# Parse number of nodes from command-line
num_nodes = int(sys.argv[1]) if len(sys.argv) > 1 and sys.argv[1].isdigit() else 1
# Total worker processes
total_workers = num_nodes * WORKERS_PER_NODE
# Requests per worker
reqs_per_worker = NUM_REQUESTS // total_workers

class RedisInsultClient:
    def __init__(self, host=REDIS_HOST, port=REDIS_PORT):
        self.r = redis.Redis(host=host, port=port, decode_responses=True)

    def insult_me(self):
        cmd = json.dumps({'method': 'insult', 'arg': None})
        self.r.lpush(COMMAND_QUEUE, cmd)
        _, raw = self.r.brpop(RESPONSE_QUEUE)
        return json.loads(raw).get('insult')


def worker_task(start_event):
    client = RedisInsultClient()
    # wait until main process signals start
    start_event.wait()
    for _ in range(reqs_per_worker):
        client.insult_me()

if __name__ == '__main__':
    # Use multiprocessing Event to sync start across processes
    start_event = multiprocessing.Event()
    processes = [multiprocessing.Process(target=worker_task, args=(start_event,))
                 for _ in range(total_workers)]

    print(f"Launching {total_workers} worker processes, each sending {reqs_per_worker} requests ({total_workers * reqs_per_worker} total)")

    # Start all worker processes
    for p in processes:
        p.start()

    # Warm-up: single request to initialize server connections
    RedisInsultClient().insult_me()

    # Begin timing
    t0 = time.perf_counter()
    start_event.set()  # signal all workers to start

    # Wait for all processes to finish
    for p in processes:
        p.join()

    t1 = time.perf_counter()
    total_time = t1 - t0
    avg_time = total_time / (total_workers * reqs_per_worker)
    requests_per_second = (total_workers * reqs_per_worker) / total_time


    print(f"Executed {total_workers * reqs_per_worker} requests in {total_time:.2f} seconds")
    print(f"Requests per second: {requests_per_second:.2f} req/s")
