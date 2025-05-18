import sys
import threading
import time
import random
import redis

# Redis configuration
REDIS_HOST = 'localhost'
REDIS_PORT = 6379
INSULTS_SET_KEY = 'insults'
PUBSUB_CHANNEL = 'insults_channel'
BROADCAST_INTERVAL = 5  # seconds

# Initialize Redis client
r = redis.Redis(host=REDIS_HOST, port=REDIS_PORT, decode_responses=True)

# Broadcaster thread: picks a random insult and publishes to channel
def broadcaster():
    while True:
        if r.scard(INSULTS_SET_KEY) > 0:
            insults = list(r.smembers(INSULTS_SET_KEY))
            insult = random.choice(insults)
            r.publish(PUBSUB_CHANNEL, insult)
            print(f"Broadcasted insult: {insult}")
        time.sleep(BROADCAST_INTERVAL)

# Command-line interface for the insult server
if __name__ == '__main__':
    # Start broadcaster thread\    threading.Thread(target=broadcaster, daemon=True).start()
    print("Insult server started. Available commands: add <insult>, get, random, exit")
    while True:
        try:
            line = input('> ').strip()
        except (EOFError, KeyboardInterrupt):
            print("Shutting down insult server.")
            break
        if not line:
            continue
        parts = line.split(maxsplit=1)
        cmd = parts[0].lower()
        arg = parts[1] if len(parts) > 1 else None
        if cmd == 'add' and arg:
            r.sadd(INSULTS_SET_KEY, arg)
            print(f"Added insult: {arg}")
        elif cmd == 'get':
            insults = r.smembers(INSULTS_SET_KEY)
            print(f"Insults: {insults}")
        elif cmd in ('random', 'insult'):
            if r.scard(INSULTS_SET_KEY) == 0:
                print("NoInsultsSaved")
            else:
                insult = random.choice(list(r.smembers(INSULTS_SET_KEY)))
                print(insult)
        elif cmd == 'exit':
            print("Shutting down insult server.")
            break
        else:
            print("Unknown command. Use add <insult>, get, random, or exit.")