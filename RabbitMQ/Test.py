import time
import sys
import subprocess as sp
import multiprocessing as mp
import signal
from rapi import RabbitMQ_ClientAPI

## Configuration parameters trough arguments
# 0 for dynamic load balancing, >0 for static number of nodes
NUM_OF_NODES = int(sys.argv[1]) if len(sys.argv) > 1 and int(sys.argv[1]) > 0 else 0

## Hard configuration parameters
INSULT_MANAGER_QUEUE = 'insult_manager'
INSULT_FILTER_QUEUE = 'insult_filter'

TOTAL_NUM_REQS = 5_000
NUM_OF_CLIENTS = 8
_REQS_PER_CLIENT = int(TOTAL_NUM_REQS / (NUM_OF_CLIENTS))

## Global variables
_clients = []
_flooders = []

def spawnServers(num_nodes:int):
    p = sp.Popen([sys.executable, "ServerManager.py", str(num_nodes)],
                 stdout=sp.PIPE,
                 stderr=sp.PIPE,
                 universal_newlines=True)
    return p

def client(queue:str, method:str, reps:int):
    rapi = RabbitMQ_ClientAPI(method_queue=queue)
    for _ in range(reps):
        rapi.call(method)

def spawnClients(num_clients:int, queue:str, method:str, reps:int):
    global _clients
    for _ in range(num_clients):
        p = mp.Process(target=client, args=(queue, method, reps))
        p.start()
        _clients.append(p)

def waitForClients():
    global _clients
    for client in _clients:
        client.join()

def floader(queue:str, method:str, reps:int):
    rapi = RabbitMQ_ClientAPI(method_queue=queue)
    rapi.flood(reps=reps, method_name=method)

def spawnFloaders(num_clients:int, queue:str, method:str, reps:int):
    global _flooders
    for _ in range(num_clients):
        p = mp.Process(target=floader, args=(queue, method, reps))
        p.start()
        _flooders.append(p)

def waitForFloader():
    global _flooders
    for f in _flooders:
        f.join()

def floadTest():
    print("Flooding the server with ", TOTAL_NUM_REQS, " \"insultMe\" reqs (", NUM_OF_CLIENTS, "w x ", _REQS_PER_CLIENT, "reqs each) to measure how long it takes to empty...")
    spawnFloaders(num_clients=NUM_OF_CLIENTS, queue=INSULT_MANAGER_QUEUE ,method="insultMe", reps=_REQS_PER_CLIENT)
    waitForFloader()

    rapi = RabbitMQ_ClientAPI(method_queue=INSULT_MANAGER_QUEUE)
    q = rapi.channel.queue_declare(queue=INSULT_MANAGER_QUEUE).method
    reqs = q.message_count
    print("Filled work queue with ", reqs, "reqs (test starts in 5 s)")
    time.sleep(5)
    print("Starting the servers and measuring how long it takes them to empty the work queue")
    delta = time.time()
    serverMng = spawnServers(NUM_OF_NODES)
    while q.message_count > 0: print("Reqs: ", q.message_count); rapi.connection.process_data_events(time_limit=0)
    delta = time.time() - delta

    print("Work queue empty, processing data...")
    print("RES: Made ", reqs, " reqs in ", delta, "s. Got an average of ", (reqs/delta), "reqs/s")

    print("Stoping the servers...")
    print("Ports used for -> This: ", mp.current_process().pid, " | serverMng: ", serverMng.pid)
    serverMng.send_signal(signal.SIGTERM)
    time.sleep(5)
    try: serverMng.terminate()
    except: pass
    print("Servers stopped.")

def clientTest():
    print("Starting servers in ", f"static({NUM_OF_NODES})" if (NUM_OF_NODES > 0) else "dynamic", " mode...")
    serverMng = spawnServers(NUM_OF_NODES)
    time.sleep(2)
    
    print("Starting Insult test... (making every worker(", NUM_OF_CLIENTS , ") do ", _REQS_PER_CLIENT, " reqs)")
    delta = time.time()
    spawnClients(num_clients=NUM_OF_CLIENTS, queue=INSULT_MANAGER_QUEUE ,method="insultMe", reps=_REQS_PER_CLIENT)
    waitForClients()
    delta = time.time() - delta
    
    print("Test finished, preparing results...")
    reqs = NUM_OF_CLIENTS*_REQS_PER_CLIENT
    print("RES: Made ", reqs, " reqs in ", delta, "s. Got an average of ", (reqs/delta), "reqs/s")

    print("Stoping the servers...")
    print("Ports used for -> This: ", mp.current_process().pid, " | serverMng: ", serverMng.pid)
    serverMng.send_signal(signal.SIGTERM)
    time.sleep(5)
    try: serverMng.terminate()
    except: pass
    print("Servers stopped.")

if __name__=='__main__':
    clientTest()