import sys
import threading
import time
import re
import redis

# Configuration
_INSULT_LIST_TTL = 5 * 60  # 5 minutes
REDIS_HOST = 'localhost'
REDIS_PORT = 6379
INSULTS_SET_KEY = 'insults'
FILTERED_LIST_KEY = 'filtered_texts'

# Initialize Redis client
r = redis.Redis(host=REDIS_HOST, port=REDIS_PORT, decode_responses=True)

# Compile dummy
pattern = re.compile("$")
# Store filtered results in Redis list
# Periodically update the insult pattern

def update_insults():
    global pattern
    while True:
        try:
            insults = r.smembers(INSULTS_SET_KEY)
            sorted_insults = sorted(insults, key=len, reverse=True)
            escaped = [re.escape(w) for w in sorted_insults]
            pattern = re.compile(r"\b(" + "|".join(escaped) + r")\b", flags=re.IGNORECASE)
            print(f"[Filter] Updated insult pattern with {len(escaped)} words")
        except Exception as e:
            print(f"[Filter] Error updating insults: {e}")
        time.sleep(_INSULT_LIST_TTL)

# Start updater thread
t = threading.Thread(target=update_insults, daemon=True)
t.start()

# Command-line interface
def main():
    print("Filter server started. Commands: filter <text>, get, exit")
    while True:
        try:
            line = input('> ').strip()
        except (EOFError, KeyboardInterrupt):
            print("Shutting down filter server.")
            break
        if not line:
            continue
        parts = line.split(maxsplit=1)
        cmd = parts[0].lower()
        arg = parts[1] if len(parts) > 1 else None

        if cmd == 'filter' and arg:
            filtered = pattern.sub('CENSORED', arg)
            r.rpush(FILTERED_LIST_KEY, filtered)
            print(filtered)
        elif cmd == 'get':
            results = r.lrange(FILTERED_LIST_KEY, 0, -1)
            for i, txt in enumerate(results, 1):
                print(f"{i}. {txt}")
        elif cmd == 'exit':
            print("Shutting down filter server.")
            break
        else:
            print("Unknown command. Use filter <text>, get, or exit.")

if __name__ == '__main__':
    main()