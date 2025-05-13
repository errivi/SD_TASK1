import sys
import threading
import time
import random
import redis

# Configuration
REDIS_HOST = 'localhost'
REDIS_PORT = 6379
INSULTS_SET_KEY = 'insults'
PUBSUB_CHANNEL = 'insults_channel'
BROADCAST_INTERVAL = 5  # seconds

# Initialize Redis client
r = redis.Redis(host=REDIS_HOST, port=REDIS_PORT, decode_responses=True)

# Broadcaster thread: picks random insult and publishes to channel
def broadcaster():
    while True:
        if r.scard(INSULTS_SET_KEY) > 0:
            insult = random.choice(r.smembers(INSULTS_SET_KEY))
            r.publish(PUBSUB_CHANNEL, insult)
            print(f"Broadcasted insult: {insult}")
        time.sleep(BROADCAST_INTERVAL)

# Command-line API for server management
def main():
    # Start broadcaster
    threading.Thread(target=broadcaster, daemon=True).start()
    print("Insult server started. Enter commands (add, get, random, exit).")
    try:
        while True:
            cmd = input('> ').strip().split(maxsplit=1)
            action = cmd[0].lower()
            arg = cmd[1] if len(cmd) > 1 else None

            if action == 'add' and arg:
                r.sadd(INSULTS_SET_KEY, arg)
                print(f"Added insult: {arg}")
            elif action == 'get':
                insults = r.smembers(INSULTS_SET_KEY)
                print(f"Insults: {insults}")
            elif action in ('random', 'insult'):
                if r.scard(INSULTS_SET_KEY) == 0:
                    print("NoInsultsSaved")
                else:
                    insult = random.choice(r.smembers(INSULTS_SET_KEY))
                    print(insult)
            elif action == 'exit':
                print("Shutting down server.")
                break
            else:
                print("Unknown command. Use add <insult>, get, random, or exit.")
    except KeyboardInterrupt:
        print("Server interrupted, exiting.")

if __name__ == '__main__':
    main()