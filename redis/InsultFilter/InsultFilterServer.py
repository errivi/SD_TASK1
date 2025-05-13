#!/usr/bin/env python3
import re
import sys
import redis

# Redis configuration
REDIS_HOST = 'localhost'
REDIS_PORT = 6379
INSULTS_SET_KEY = 'insults'
FILTERED_LIST_KEY = 'filtered_texts'

# Connect to Redis
r = redis.Redis(host=REDIS_HOST, port=REDIS_PORT, decode_responses=True)

print("InsultFilter server started. Enter commands (filter <text>, get, exit).")

while True:
    try:
        line = input('> ').strip()
    except (EOFError, KeyboardInterrupt):
        print("Shutting down server.")
        break

    if not line:
        continue
    parts = line.split(maxsplit=1)
    cmd = parts[0].lower()
    arg = parts[1] if len(parts) > 1 else None

    if cmd == 'filter' and arg:
        # Fetch current insults
        insults = r.smembers(INSULTS_SET_KEY)
        # Order by length (longest first) to avoid partial matches
        sorted_insults = sorted(insults, key=len, reverse=True)
        # Build regex pattern
        pattern = re.compile(r"\b(" + "|".join(re.escape(w) for w in sorted_insults) + r")\b",
                             flags=re.IGNORECASE)
        # Replace insults with 'CENSORED'
        filtered = pattern.sub('CENSORED', arg)
        # Store filtered text in Redis list
        r.rpush(FILTERED_LIST_KEY, filtered)
        print(filtered)

    elif cmd == 'get':
        # Get all filtered texts
        results = r.lrange(FILTERED_LIST_KEY, 0, -1)
        for idx, txt in enumerate(results, 1):
            print(f"{idx}. {txt}")

    elif cmd == 'exit':
        print("Shutting down server.")
        break

    else:
        print("Unknown command. Use filter <text>, get, or exit.")