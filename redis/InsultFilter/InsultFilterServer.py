# filter_server.py
#!/usr/bin/env python3
import redis
import time
import json
import re

# In-memory insults storage
insults = ["clown", "blockhead", "dimwit", "nincompoop", "simpleton", "dullard", "buffoon", "nitwit", "half-wit",
           "scatterbrain", "scatterbrained", "knucklehead", "dingbat", "doofus", "ninny", "ignoramus", "muttonhead",
           "bonehead", "airhead", "puddingbrain", "mushbrain", "blockhead", "dunderhead", "lamebrain", "muttonhead",
           "numbskull", "dimwit", "dullard", "fool", "goofball", "knucklehead", "lunkhead", "maroon", "mook",
           "nincompoop", "ninnyhammer", "numskull", "patzer", "puddingbrain", "sap", "simpleton", "scofflaw",
           "screwball", "twit", "woozle", "yahoo", "zany"]

# Configuration
REDIS_HOST = 'localhost'
REDIS_PORT = 6379
COMMAND_QUEUE = 'filter_channel'
RESPONSE_QUEUE = 'filter_response_queue'

# In-memory storage for filtered texts
filtered_texts = []

# Compile regex pattern once (word boundaries + case-insensitive)
_pattern = re.compile(
    r"\b(?:" + "|".join(re.escape(word) for word in insults) + r")(?:\w*)\b",
    flags=re.IGNORECASE
)

# Redis connection for queue
r = redis.Redis(host=REDIS_HOST, port=REDIS_PORT, decode_responses=True)

def filter_text(text):
    filtered_version = _pattern.sub("CENSORED", text)
    # Append only if different from the last entry to avoid duplicates
    if not filtered_texts or filtered_texts[-1] != filtered_version:
        filtered_texts.append(filtered_version)
    return filtered_version

# Processor: handle commands and respond
def processor():
    print("Starting filter processor...")
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
            case 'filter' if arg:
                filtered = filter_text(arg)
                response = json.dumps({'filtered': filtered})
                r.lpush(RESPONSE_QUEUE, response)
                print(f"[Processor] filtered text: {filtered}")

            case 'getFiltered':
                response = json.dumps({'filtered_list': filtered_texts})
                r.lpush(RESPONSE_QUEUE, response)
                print(f"[Processor] returned filtered text list")

            case _:
                print(f"[Processor] unknown method or missing argument: {cmd}")

if __name__ == '__main__':
    try:
        processor()
    except KeyboardInterrupt:
        print("Filter server stopped")