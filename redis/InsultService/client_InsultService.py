# client.py
#!/usr/bin/env python3
import redis
import threading
import time
import json

# Configuration
REDIS_HOST = 'localhost'
REDIS_PORT = 6379
COMMAND_QUEUE = 'insult_channel'         # Queue for sending commands to server
RESPONSE_QUEUE = 'insult_response_queue' # Queue for receiving responses from server
PUBSUB_CHANNEL = 'insults_broadcast'    # Channel for server broadcasts

class RedisInsultClient:
    def __init__(self, host=REDIS_HOST, port=REDIS_PORT):
        self.r = redis.Redis(host=host, port=port, decode_responses=True)

    def add_insult(self, insult):
        # Send 'add' command to server
        cmd = json.dumps({'method': 'add', 'arg': insult})
        self.r.lpush(COMMAND_QUEUE, cmd)
        print(f"-> Sent ADD command '{insult}' to server")

    def get_insults(self):
        # Send 'get' command and wait for server response
        cmd = json.dumps({'method': 'get', 'arg': None})
        self.r.lpush(COMMAND_QUEUE, cmd)
        # Block until server responds
        _, raw = self.r.brpop(RESPONSE_QUEUE)
        response = json.loads(raw)
        insults = response.get('insults', [])
        print(f"get_insults() -> {insults}")
        return insults

    def insult_me(self):
        # Send 'insult' command and wait for server response
        cmd = json.dumps({'method': 'insult', 'arg': None})
        self.r.lpush(COMMAND_QUEUE, cmd)
        # Block until server responds
        _, raw = self.r.brpop(RESPONSE_QUEUE)
        response = json.loads(raw)
        insult = response.get('insult')
        if insult is None:
            print("insult_me() -> NoInsultsAvailable")
            return None
        print(f"insult_me() -> {insult}")
        return insult

    def subscribe_insults(self):
        # Subscribe to broadcast channel and print messages
        pubsub = self.r.pubsub(ignore_subscribe_messages=True)
        pubsub.subscribe(PUBSUB_CHANNEL)
        print(f"Subscribed to channel '{PUBSUB_CHANNEL}'. Waiting for insults...")
        for message in pubsub.listen():
            print(f"[Broadcast] {message['data']}")

if __name__ == '__main__':
    client = RedisInsultClient()

    print("\n--- Basic Tests ---")
    client.get_insults()
    client.insult_me()

    print("\n--- Adding insults via queue ---")
    for ins in ['clown', 'blockhead', 'dimwit']:
        client.add_insult(ins)
        time.sleep(0.1)

    print("\n--- Retrieving insults from server ---")
    client.get_insults()

    print("\n--- Random insult tests ---")
    for _ in range(5):
        client.insult_me()
        time.sleep(0.2)

    # Start subscription thread
    t = threading.Thread(target=client.subscribe_insults, daemon=True)
    t.start()

    try:
        while True:
            time.sleep(1)
    except KeyboardInterrupt:
        print("Client stopped")