import sys
import redis
import re

# Redis configuration
REDIS_HOST = 'localhost'
REDIS_PORT = 6379
INSULTS_SET_KEY = 'insults'
FILTERED_LIST_KEY = 'filtered_texts'

class InsultFilterClient:
    def __init__(self):
        self.r = redis.Redis(host=REDIS_HOST, port=REDIS_PORT, decode_responses=True)

    def filter_text(self, text):
        # Build regex from insults set
        insults = self.r.smembers(INSULTS_SET_KEY)
        sorted_insults = sorted(insults, key=len, reverse=True)
        escaped = [re.escape(w) for w in sorted_insults]
        pattern = re.compile(r"(" + "|".join(escaped) + r")", flags=re.IGNORECASE)
        filtered = pattern.sub('CENSORED', text)
        # Store filtered result
        self.r.rpush(FILTERED_LIST_KEY, filtered)
        return filtered

    def get_filtered_texts(self):
        return self.r.lrange(FILTERED_LIST_KEY, 0, -1)

if __name__ == '__main__':
    if len(sys.argv) < 2:
        print("Usage: python FilterClient.py <text_to_filter>")
        sys.exit(1)
    text_to_filter = sys.argv[1]
    client = InsultFilterClient()
    try:
        filtered_text = client.filter_text(text_to_filter)
        print("Non filtered text:", text_to_filter, "Filtered text:", filtered_text)
        all_filtered_texts = client.get_filtered_texts()
        print("Filtered text list:")
        for idx, item in enumerate(all_filtered_texts, start=1):
            print(f"{idx}. {item}")
    except Exception as e:
        print("Error communicating with Redis filter server:", e)
