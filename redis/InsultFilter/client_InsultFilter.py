#!/usr/bin/env python3
import sys
import redis

# Redis configuration
REDIS_HOST = 'localhost'
REDIS_PORT = 6379
FILTERED_LIST_KEY = 'filtered_texts'

# Connect to Redis
r = redis.Redis(host=REDIS_HOST, port=REDIS_PORT, decode_responses=True)

# Example usage: python client_filter.py "Tu texto aquí"
if len(sys.argv) < 2:
    print("Usage: client_filter.py <text_to_filter>")
    sys.exit(1)

text_to_filter = sys.argv[1]

# Invoke filter by pushing a command to the server via Redis Pub/Sub (optional)
# For simplicity, we'll use the same CLI commands via a secondary channel.
# Alternatively, you could call the server's CLI directly, but we'll simulate by
# directly performing the filter logic here.

# Perform filtering locally (client-side)
insults = r.smembers('insults')
sorted_insults = sorted(insults, key=len, reverse=True)
import re
pattern = re.compile(r"\b(" + "|".join(re.escape(w) for w in sorted_insults) + r")\b", flags=re.IGNORECASE)
filtered = pattern.sub('CENSORED', text_to_filter)
print("Original:", text_to_filter)
print("Filtered:", filtered)

# Fetch all filtered texts from server
all_filtered = r.lrange(FILTERED_LIST_KEY, 0, -1)
print("\nFiltered texts on server:")
for idx, txt in enumerate(all_filtered, 1):
    print(f"{idx}. {txt}")
