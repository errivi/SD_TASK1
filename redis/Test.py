import sys
import redis
import multiprocessing
import time
import random
import re


NUM_OF_NODES = int(sys.argv[1]) if len(sys.argv) > 1 and int(sys.argv[1]) > 1 else 1

# Redis configuration
REDIS_HOST = 'localhost'
REDIS_PORT = 6379
INSULTS_KEY = 'insults'
FILTERED_LIST_KEY = 'filtered_results'

# Test parameters
REQS_PER_PHASE = 200_000
WORKERS_PER_NODE = 8
N_PROCESSES = NUM_OF_NODES * WORKERS_PER_NODE
REQS_PER_PROCESS = REQS_PER_PHASE // N_PROCESSES

# Initial Redis connection and data preparation
r = redis.Redis(host=REDIS_HOST, port=REDIS_PORT, decode_responses=True)
r.flushdb()
insults = ["clown", "blockhead", "dimwit", "nincompoop", "simpleton", "dullard", "buffoon", "nitwit", "half-wit",
           "scatterbrain", "scatterbrained", "knucklehead", "dingbat", "doofus", "ninny", "ignoramus", "muttonhead",
           "bonehead", "airhead", "puddingbrain", "mushbrain", "blockhead", "dunderhead", "lamebrain", "muttonhead",
           "numbskull", "dimwit", "dullard", "fool", "goofball", "knucklehead", "lunkhead", "maroon", "mook",
           "nincompoop", "ninnyhammer", "numskull", "patzer", "puddingbrain", "sap", "simpleton", "scofflaw",
           "screwball", "twit", "woozle", "yahoo", "zany"]
r.sadd(INSULTS_KEY, *insults)


phrases = []
base_templates = [
    "It's genuinely impressive how you manage to sound like a complete %s every single time you open your mouth.",
    "You just wrote an entire paragraph that proves, without a shadow of a doubt, you're a world-class %s with no competition.",
    "Every time I read one of your comments, I lose a few brain cells and start to believe that being a %s might actually be contagious.",
    "You really woke up this morning, looked in the mirror, and decided, 'Yes, today I will be the most insufferable %s anyone has ever met.'",
    "I’ve seen bad takes before, but this one is so profoundly idiotic that even a %s would be embarrassed to claim it.",
    "Somewhere out there, a committee of %ss is applauding you for pushing the boundaries of what it means to be completely useless.",
    "If there were a museum of stupidity, your statement would be proudly framed under the section titled 'Legendary %s Moments'.",
    "Your entire thought process reads like it was written by a team of %ss trying to outdo each other in a competition of pure nonsense.",
    "This level of delusion and arrogance combined is only achievable by someone who has fully embraced their identity as a %s and made it their personal brand.",
    "I used to think no one could truly embody the definition of a %s so completely—until you came along and shattered all expectations.",
    "You are a piece of %s, %s, and you're mum is %s,%s,%s,%s,%s,%s",
    "I like programming this practice and also the second one that i won't have time until exams ends"
]
for tmpl in base_templates:
    n = tmpl.count("%s")            # count placeholders
    for _ in insults:
        picks = random.sample(insults, n)
        phrases.append(tmpl % tuple(picks))


def insult_worker(n):
    rc = redis.Redis(host=REDIS_HOST, port=REDIS_PORT, decode_responses=True)
    for _ in range(n):
        rc.srandmember(INSULTS_KEY)


def filter_worker(n):
    rc = redis.Redis(host=REDIS_HOST, port=REDIS_PORT, decode_responses=True)
    pat = None
    for _ in range(n):
        if pat is None:
            current = rc.smembers(INSULTS_KEY)
            esc = [re.escape(w) for w in current]
            pat = re.compile(r"\b(" + "|".join(esc) + r")\b", flags=re.IGNORECASE)
        text = random.choice(phrases)
        pat.sub("CENSORED", text)
        rc.rpush(FILTERED_LIST_KEY, text)

if __name__ == "__main__":
    print(f"Test Redis with {NUM_OF_NODES} node(s), {N_PROCESSES} processes ({WORKERS_PER_NODE} per node), {REQS_PER_PHASE} reqs per fase")

    # Phase 1: insult
    procs = []
    start = time.perf_counter()
    for _ in range(N_PROCESSES):
        p = multiprocessing.Process(target=insult_worker, args=(REQS_PER_PROCESS,))
        p.start()
        procs.append(p)
    for p in procs:
        p.join()
    elapsed = time.perf_counter() - start
    rps = REQS_PER_PHASE / elapsed
    print(f"Phase 1: {REQS_PER_PHASE} calls in {elapsed:.2f}s -> {rps:.2f} req/s")

    # Phase 2: filter
    r.delete(FILTERED_LIST_KEY)
    procs = []
    start = time.perf_counter()
    for _ in range(N_PROCESSES):
        p = multiprocessing.Process(target=filter_worker, args=(REQS_PER_PROCESS,))
        p.start()
        procs.append(p)
    for p in procs:
        p.join()
    elapsed = time.perf_counter() - start
    rps = REQS_PER_PHASE / elapsed
    print(f"Phase 2: {REQS_PER_PHASE} calls in {elapsed:.2f}s -> {rps:.2f} req/s")
