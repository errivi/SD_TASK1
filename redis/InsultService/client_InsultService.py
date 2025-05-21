#!/usr/bin/env python3
import redis
import random
import time

# Initial configuration
REDIS_HOST = 'localhost'
REDIS_PORT = 6379
INSULTS_KEY = 'insults'
PUBSUB_CHANNEL = 'insults_channel'

class RedisInsultClient:
    def __init__(self, host=REDIS_HOST, port=REDIS_PORT):
        self.r = redis.Redis(host=host, port=port, decode_responses=True)

    def add_insult(self, insult):
        added = self.r.sadd(INSULTS_KEY, insult)
        print(f"add('{insult}') -> {'added' if added else 'already existed'}")

    def get_insults(self):
        insults = list(self.r.smembers(INSULTS_KEY))
        print(f"get() -> {insults}")
        return insults

    def insult_me(self):
        count = self.r.scard(INSULTS_KEY)
        if count == 0:
            print("insult() -> NoInsultsSaved")
            return None
        insult = self.r.srandmember(INSULTS_KEY)
        print(f"insult() -> {insult}")
        return insult

    def clear_insults(self):
        self.r.delete(INSULTS_KEY)
        print("clear_insults() -> done")

if __name__ == "__main__":
    client = RedisInsultClient()

    print("\n--- Initial clean ---")
    client.clear_insults()

    print("\n--- test: get() empty ---")
    client.get_insults()

    print("\n--- test: insult() empty ---")
    client.insult_me()

    print("\n--- test: add_insult() & get() ---")
    sample = ["clown", "blockhead", "dimwit", "nincompoop"]
    for ins in sample:
        client.add_insult(ins)
    client.get_insults()

    print("\n--- test: add duplicated ---")
    client.add_insult("clown")  # existing insult

    print("\n--- test: insult_me() multiple times ---")
    for _ in range(5):
        client.insult_me()
        time.sleep(0.2)

    print("\n--- Test end ---")
