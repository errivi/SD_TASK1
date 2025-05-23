# stress_test_client.py
#!/usr/bin/env python3
import redis
import json
import time

NUM_OF_NODES = int(sys.argv[1]) if len(sys.argv) > 1 and int(sys.argv[1]) > 1 else 1

# Configuration
REDIS_HOST = 'localhost'
REDIS_PORT = 6379
COMMAND_QUEUE = 'insult_channel'
RESPONSE_QUEUE = 'insult_response_queue'
NUM_REQUESTS = 200_000

# Test parameters
WORKERS_PER_NODE = 8
REQS_PER_WORKER = NUM_REQUESTS // WORKERS_PER_NODE

class RedisInsultClient:
    def __init__(self, host=REDIS_HOST, port=REDIS_PORT):
        self.r = redis.Redis(host=host, port=port, decode_responses=True)

    def insult_me(self):
        # Send 'insult' command and wait for response
        cmd = json.dumps({'method': 'insult', 'arg': None})
        self.r.lpush(COMMAND_QUEUE, cmd)
        _, raw = self.r.brpop(RESPONSE_QUEUE)
        response = json.loads(raw)
        return response.get('insult')

if __name__ == '__main__':
    client = RedisInsultClient()

    # Warm-up: single request
    _ = client.insult_me()

    # Stress test
    start = time.perf_counter()
    for _ in range(NUM_REQUESTS):
        client.insult_me()
    end = time.perf_counter()

    total_time = end - start
    avg_time = total_time / NUM_REQUESTS

    print(f"Executed {NUM_REQUESTS} requests in {total_time:.2f} seconds")
    print(f"Average time per request: {avg_time * 1000:.4f} ms")