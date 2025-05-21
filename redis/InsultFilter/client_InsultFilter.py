#!/usr/bin/env python3
import redis
import re
import sys
import time

# Redis configuration
REDIS_HOST = 'localhost'
REDIS_PORT = 6379
INSULTS_KEY = 'insults'
FILTERED_LIST_KEY = 'filtered_texts'

class RedisFilterClient:
    def __init__(self, host=REDIS_HOST, port=REDIS_PORT):
        self.r = redis.Redis(host=host, port=port, decode_responses=True)
        # Pre-build pattern once on init
        self._compile_pattern()

    def _compile_pattern(self):
        insults = self.r.smembers(INSULTS_KEY)
        sorted_insults = sorted(insults, key=len, reverse=True)
        escaped = [re.escape(w) for w in sorted_insults]
        if escaped:
            pattern_str = r"\b(" + "|".join(escaped) + r")\b"
            self.pattern = re.compile(pattern_str, flags=re.IGNORECASE)
        else:
            # No insults yet: match nothing
            self.pattern = re.compile(r"(?!x)x")

    def filter_text(self, text):
        filtered = self.pattern.sub("CENSORED", text)
        self.r.rpush(FILTERED_LIST_KEY, filtered)
        return filtered

    def get_filtered_texts(self):
        return self.r.lrange(FILTERED_LIST_KEY, 0, -1)

    def clear_filtered(self):
        self.r.delete(FILTERED_LIST_KEY)

    def refresh_insults(self):
        self._compile_pattern()

if __name__ == "__main__":
    client = RedisFilterClient()

    # Prepare test data
    print("\n--- Clearing existing filtered results ---")
    client.clear_filtered()

    print("\n--- Current insults set ---")
    insults = list(client.r.smembers(INSULTS_KEY))
    print(insults if insults else "(empty)")

    # Sample phrases to test
    sample_phrases = [
        "You are such a clown, always clowning around.",
        "I can't believe that doofus just did that.",
        "This is a perfectly innocent sentence.",
        "Only a buffoon would think that's a good idea.",
        "Nothing to censor here."
    ]

    # Filter each phrase
    print("\n--- Filtering sample phrases ---")
    for phrase in sample_phrases:
        # optionally recompile if insults may have changed
        client.refresh_insults()
        result = client.filter_text(phrase)
        print(f"Input:    {phrase}\nFiltered: {result}\n")

    # Retrieve all filtered texts
    print("\n--- All filtered texts stored in Redis ---")
    for idx, txt in enumerate(client.get_filtered_texts(), start=1):
        print(f"{idx}. {txt}")

    print("\n--- Test completed ---")
