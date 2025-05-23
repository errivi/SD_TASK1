import pika
import time
import sys
import subprocess as sp
import multiprocessing as mp
import signal

## Configuration parameters trough arguments
# 0 for dynamic load balancing, >0 for static number of nodes
NUM_OF_NODES = int(sys.argv[1]) if len(sys.argv) > 1 and int(sys.argv[1]) > 0 else 0

## Hard configuration parameters
INSULT_MANAGER_QUEUE = 'insult_manager'
INSULT_FILTER_QUEUE = 'insult_filter'

TOTAL_NUM_REQS = 2_000_000
NUM_OF_CLIENTS = 6
_REQS_PER_CLIENT = int(TOTAL_NUM_REQS / (NUM_OF_CLIENTS))# if NUM_OF_NODES > 0 else 1_000

## Global variables
_clients = []

def spawnServers(num_nodes:int):
    p = sp.Popen([sys.executable, "ServerManager.py", str(num_nodes)],
                 stdout=sp.PIPE,
                 stderr=sp.PIPE,
                 universal_newlines=True)
    return p

def client(queue:str, method:str, reps:int):
    rapi = pika.BlockingConnection(pika.ConnectionParameters(heartbeat=300))
    rapi = rapi.channel()
    send_properties = pika.BasicProperties(type=method, delivery_mode=2)
    for _ in range(reps):
        rapi.basic_publish(
            exchange='',
            routing_key=queue,
            body="",
            properties=send_properties
        )

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

if __name__=='__main__':
    #print("Starting servers in ", f"static({NUM_OF_NODES})" if (NUM_OF_NODES > 0) else "dynamic", " mode...")
    #serverMng = spawnServers(NUM_OF_NODES)
    #time.sleep(2)

    print("Floading the work queue... (making every worker(", NUM_OF_CLIENTS , ") do ", _REQS_PER_CLIENT, " reqs)")
    spawnClients(num_clients=NUM_OF_CLIENTS, queue=INSULT_MANAGER_QUEUE ,method="insultMe", reps=_REQS_PER_CLIENT)
    waitForClients()
    
    print("Queue filled.")
    reqs = NUM_OF_NODES*NUM_OF_CLIENTS*_REQS_PER_CLIENT
    print("RES: Made ", reqs, " reqs")

    #print("Stoping the servers...")
    #print("Ports used for -> This: ", mp.current_process().pid, " | serverMng: ", serverMng.pid)
    #serverMng.send_signal(signal.SIGTERM)
    #time.sleep(5)
    #try: serverMng.kill()
    #except: pass
    #print("Servers stopped.")