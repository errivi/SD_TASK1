import sys
import redis
import multiprocessing
import time
import random
import re

# Leer número de "nodos" (lógicos) por parámetro
NUM_OF_NODES = int(sys.argv[1]) if len(sys.argv) > 1 and int(sys.argv[1]) > 1 else 1

# Redis configuration
REDIS_HOST = 'localhost'
REDIS_PORT = 6379
INSULTS_KEY = 'insults'
FILTERED_LIST_KEY = 'filtered_results'

# Test parameters
TOTAL_REQS = 200_000
# Mitad de peticiones para insult y mitad para filter
REQS_PER_PHASE = TOTAL_REQS // 2
# Número de procesos por nodo lógico
WORKERS_PER_NODE = 8
# Total de procesos
N_PROCESSES = NUM_OF_NODES * WORKERS_PER_NODE
# Cada proceso procesa
REQS_PER_PROCESS = REQS_PER_PHASE // N_PROCESSES

# Conexión inicial a Redis y preparación de datos
r = redis.Redis(host=REDIS_HOST, port=REDIS_PORT, decode_responses=True)
r.flushdb()
insults = ["idiota", "tonto", "imbecil", "estupido", "bobo", "loco"]
r.sadd(INSULTS_KEY, *insults)

# Construir frases de prueba
phrases = []
base_templates = [
    "Eres un %s en potencia",
    "Qué comentario más %s",
    "Ese comportamiento es de un %s",
    "%s total"
]
for tmpl in base_templates:
    for ins in insults:
        phrases.append(tmpl % ins)

# Worker para obtener insultos aleatorios
def insult_worker(n):
    rc = redis.Redis(host=REDIS_HOST, port=REDIS_PORT, decode_responses=True)
    for _ in range(n):
        rc.srandmember(INSULTS_KEY)

# Worker para filtrar frases
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
    print(f"Test Redis con {NUM_OF_NODES} nodo(s) lógicos, {N_PROCESSES} procesos ({WORKERS_PER_NODE} por nodo), {REQS_PER_PHASE} reqs por fase")

    # Fase 1: insult
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
    print(f"Fase 1: {REQS_PER_PHASE} llamadas en {elapsed:.2f}s -> {rps:.2f} req/s")

    # Fase 2: filter
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
    print(f"Fase 2: {REQS_PER_PHASE} llamadas en {elapsed:.2f}s -> {rps:.2f} req/s")
