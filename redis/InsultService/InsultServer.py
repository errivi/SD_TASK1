# server.py
#!/usr/bin/env python3
import redis
import threading
import time
import random
import json

# Configuration
REDIS_HOST = 'localhost'
REDIS_PORT = 6379
COMMAND_QUEUE = 'insult_channel'
RESPONSE_QUEUE = 'insult_response_queue'
PUBSUB_CHANNEL = 'insults_broadcast'
BROADCAST_INTERVAL = 5  # seconds

# In-memory insults storage
insults = ["clown", "blockhead", "dimwit", "nincompoop", "simpleton", "dullard", "buffoon", "nitwit", "half-wit",
           "scatterbrain", "scatterbrained", "knucklehead", "dingbat", "doofus", "ninny", "ignoramus", "muttonhead",
           "bonehead", "airhead", "puddingbrain", "mushbrain", "blockhead", "dunderhead", "lamebrain", "muttonhead",
           "numbskull", "dimwit", "dullard", "fool", "goofball", "knucklehead", "lunkhead", "maroon", "mook",
           "nincompoop", "ninnyhammer", "numskull", "patzer", "puddingbrain", "sap", "simpleton", "scofflaw",
           "screwball", "twit", "woozle", "yahoo", "zany"]

# Redis connection for pub/sub and queue
r = redis.Redis(host=REDIS_HOST, port=REDIS_PORT, decode_responses=True)

# Broadcaster thread: publishes a random insult every interval
def broadcaster():
    while True:
        if insults:
            insult = random.choice(insults)
            r.publish(PUBSUB_CHANNEL, insult)
            #print(f"[Broadcast] sent: {insult}")
        time.sleep(BROADCAST_INTERVAL)

# Processor: handles commands from queue and updates local set or responds
def processor():
    print("Starting command processor...")
    while True:
        _, raw = r.brpop(COMMAND_QUEUE)
        try:
            cmd = json.loads(raw)
            method = cmd.get('method')
            arg = cmd.get('arg')
        except json.JSONDecodeError:
            print(f"Invalid command: {raw}")
            continue
        match method:
            case 'add' if arg:
                if arg not in insults:
                    insults.add(arg)
            case 'get':
                # Respond with full list
                response = json.dumps({'insults': insults})
                r.lpush(RESPONSE_QUEUE, response)
            case 'insult':
                i = 0
                for _ in range(100_000): i += 1  # Add latency to the request to mitigate not enough clients problem
                # Respond with a random insult or None
                if insults:
                    insult = random.choice(insults)
                    response = json.dumps({'insult': insult})
                else:
                    response = json.dumps({'insult': None})
                r.lpush(RESPONSE_QUEUE, response)
            case _:
                print(f"[Processor] unknown method or missing argument: {cmd}")

if __name__ == '__main__':
    # Start broadcaster
    threading.Thread(target=broadcaster, daemon=True).start()
    # Start processor
    try:
        processor()
    except KeyboardInterrupt:
        print("Server stopped")