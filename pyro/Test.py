import sys
import subprocess
import time
import multiprocessing as mp
import Pyro4
import atexit
import signal

# Número de nodos InsultServer a arrancar (puede pasarse como argumento)
NUM_OF_NODES = int(sys.argv[1]) if len(sys.argv) > 1 and int(sys.argv[1]) > 1 else 1

BASE_INSULT_SERVER_PORT = 8000

# Listas globales de nodos y procesos cliente
_InsultNodeList = []
_clients = []

# Para guardar procesos de servidores si queremos matarlos al final
_server_processes = []
nameserver_process = None

# Configuración de test
TOTAL_REQS = 10_000
NUM_CLIENTS = 4  # número de procesos clientes por nodo

class InsultNode:
    def __init__(self, port, process):
        self.port = port
        self.process = process
        _InsultNodeList.append(self)

def spawn_insult_node():
    port = BASE_INSULT_SERVER_PORT + len(_InsultNodeList)
    # Arranca InsultServer.py con el puerto
    proc = subprocess.Popen([sys.executable, 'InsultService/InsultServer.py', str(port)])
    _server_processes.append(proc)
    return InsultNode(port, proc)

def wait_for_registration(name, timeout=10.0):
    """
    Espera hasta que el Name Server tenga registrado el nombre 'name', o timeout segundos.
    Retorna True si se registró, False si timeout o error.
    """
    try:
        ns = Pyro4.locateNS()
    except Exception as e:
        print(f"Error localizando Name Server para espera de registro de '{name}': {e}")
        return False
    start = time.time()
    while True:
        try:
            ns.lookup(name)
            return True
        except Pyro4.errors.NamingError:
            if time.time() - start > timeout:
                return False
            time.sleep(0.2)
        except Exception as e:
            if time.time() - start > timeout:
                print(f"Error al esperar registro de '{name}': {e}")
                return False
            time.sleep(0.2)

def fillServerWithInsults(port):
    insults = [
        "clown", "blockhead", "dimwit", "nincompoop", "simpleton", "dullard", "buffoon",
        "nitwit", "half-wit", "scatterbrain", "scatterbrained", "knucklehead", "dingbat",
        "doofus", "ninny", "ignoramus", "muttonhead", "bonehead", "airhead", "puddingbrain",
        "mushbrain", "dunderhead", "lamebrain", "numbskull", "fool", "goofball", "lunkhead",
        "maroon", "mook", "ninnyhammer", "numskull", "patzer", "sap", "scofflaw", "screwball",
        "twit", "woozle", "yahoo", "zany"
    ]
    proxy = Pyro4.Proxy(f"PYRO:example.InsultServer@127.0.0.1:{port}")
    for ins in insults:
        try:
            proxy.add_insult(ins)
        except Exception as e:
            print(f"Error al añadir insulto '{ins}' a servidor en puerto {port}: {e}")

def floadInsultServer(name, reqs_per_client):
    ns = Pyro4.locateNS()
    for _ in range(reqs_per_client):
        uri = ns.lookup(name)
        proxy = Pyro4.Proxy(uri)
        proxy.insult_me()

def spawnClients(name, func, reqs_per_client):
    for _ in range(NUM_CLIENTS):
        p = mp.Process(target=func, args=(name,reqs_per_client))
        _clients.append(p)
        p.start()

def waitForClients():
    for p in _clients:
        p.join()

def terminate_all():
    # Terminar procesos cliente
    for p in _clients:
        if p.is_alive():
            p.terminate()
    # Terminar procesos de servidor
    for proc in _server_processes:
        try:
            proc.terminate()
        except Exception:
            pass
    # Terminar Name Server si sigue vivo
    global nameserver_process
    try:
        if nameserver_process and nameserver_process.poll() is None:
            nameserver_process.terminate()
    except Exception:
        pass

if __name__ == '__main__':
    print("Starting Pyro Name Server...")
    nameserver_process = subprocess.Popen(
        [sys.executable, "-m", "Pyro4.naming"],
        stdout=subprocess.DEVNULL,
        stderr=subprocess.DEVNULL
    )
    atexit.register(terminate_all)
    signal.signal(signal.SIGINT, lambda signum, frame: sys.exit(0))
    signal.signal(signal.SIGTERM, lambda signum, frame: sys.exit(0))

    # Dar tiempo al Name Server a arrancar
    time.sleep(2)

    # Arrancar nodos InsultServer
    print("Spawning all the insult nodes...")
    for _ in range(NUM_OF_NODES): spawn_insult_node()

    # Calcular peticiones por cliente
    REQS_PER_CLIENT = int(TOTAL_REQS // (NUM_CLIENTS))

    # Test InsultService
    print("Filling the servers with insults...")
    for node in _InsultNodeList: fillServerWithInsults(node.port)

    print(f"Starting Insult test... (making every client do {REQS_PER_CLIENT} reqs)")
    delta = time.time()
    spawnClients("example.InsultServer", floadInsultServer, REQS_PER_CLIENT)
    waitForClients()
    delta = time.time() - delta

    print("Test finished.")
    reqs = NUM_CLIENTS * REQS_PER_CLIENT
    print(f"RES: Made {reqs} reqs in {delta:.2f} secs. Got {reqs/delta:.2f} reqs/s")

    print("Stopping all clients and servers...")
    terminate_all()
    sys.exit(0)