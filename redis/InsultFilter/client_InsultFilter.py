import redis
import json

texts_to_filter = [
    "You're such a clown, always acting the fool.",
    "Honestly, you're a blockhead who can't catch a break.",
    "That idea was as dimwitted as it gets.",
    "Stop being a nincompoop and think for a second.",
    "You're a simpleton with no sense of the bigger picture.",
]

# Configuration
REDIS_HOST = 'localhost'
REDIS_PORT = 6379
COMMAND_QUEUE = 'filter_channel'          # Queue for sending commands to filter server
RESPONSE_QUEUE = 'filter_response_queue'  # Queue for receiving responses from filter server


class RedisFilterClient:
    def __init__(self, host=REDIS_HOST, port=REDIS_PORT):
        self.r = redis.Redis(host=host, port=port, decode_responses=True)

    def filter_text(self, text):
        # Send 'filter' command and wait for response
        cmd = json.dumps({'method': 'filter', 'arg': text})
        self.r.lpush(COMMAND_QUEUE, cmd)
        _, raw = self.r.brpop(RESPONSE_QUEUE)
        response = json.loads(raw)
        filtered = response.get('filtered')
        return filtered

    def get_filtered(self):
        # Send 'getFiltered' command and wait for response
        cmd = json.dumps({'method': 'getFiltered', 'arg': None})
        self.r.lpush(COMMAND_QUEUE, cmd)
        _, raw = self.r.brpop(RESPONSE_QUEUE)
        response = json.loads(raw)
        filtered_list = response.get('filtered_list', [])
        return filtered_list

if __name__ == '__main__':
    client = RedisFilterClient()

    for phrase in texts_to_filter:
        filtered = client.filter_text(phrase)
        print(f"Original: {phrase}\nFiltered: {filtered}\n")

    all_filtered = client.get_filtered()
    print("\nAll filtered texts:")
    for idx, ft in enumerate(all_filtered, start=1):
        print(f"{idx}. {ft}")