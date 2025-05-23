from rapi import RabbitMQ_ClientAPI
import time
import sys
import subprocess as sp
import multiprocessing as mp
import signal

import pika

## Configuration parameters trough arguments
# 0 for dynamic load balancing, >0 for static number of nodes
NUM_OF_NODES = int(sys.argv[1]) if len(sys.argv) > 1 and int(sys.argv[1]) > 0 else 0

## Hard configuration parameters
INSULT_MANAGER_QUEUE = 'insult_manager'
INSULT_FILTER_QUEUE = 'insult_filter'

TOTAL_NUM_REQS = 10
NUM_OF_CLIENTS = 1
_REQS_PER_CLIENT = int(TOTAL_NUM_REQS / (NUM_OF_NODES * NUM_OF_CLIENTS)) if NUM_OF_NODES > 0 else 1_000

## Global variables
_clients = []

def spawnServers(num_nodes:int):
    p = sp.Popen([sys.executable, "ServerManager.py", str(num_nodes)],
                 stdout=sp.PIPE,
                 stderr=sp.PIPE,
                 universal_newlines=True)
    return p

def singleConnectClient(queue:str, method:str, reps:int):
    rapi = RabbitMQ_ClientAPI(method_queue=queue)
    rapi.connect()
    rapi.multicall(method=method, reps=reps)

def multiConnectClient(queue:str, method:str, reps:int):
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
    #rapi = RabbitMQ_ClientAPI(method_queue=queue)
    #rapi.connect()
    #for _ in range(reps):
    #    response = rapi.call(method=method)
    #    response.decode()

def spawnClients(num_clients:int, client_type, queue:str, method:str, reps:int):
    global _clients
    for _ in range(num_clients):
        p = mp.Process(target=client_type, args=(queue, method, reps))
        p.start()
        _clients.append(p)

def waitForClients():
    global _clients
    for client in _clients:
        client.join()

if __name__=='__main__':
    #print("Starting new rapi client...")
    #rapi = RabbitMQ_ClientAPI(method_queue=INSULT_MANAGER_QUEUE)
    #rapi.connect()
    #time.sleep(25)
    #print("Sending insultMe request to rapi...")
    #r = rapi.call("insultMe")
    #print("Got response ", r, " from rapi client doing insultMe request")
    print("Attempting 10 insultMe request burst to rabbit...")
    multiConnectClient(queue=INSULT_MANAGER_QUEUE, method="insultMe", reps=10)
    #TODO: Seems to get stuck waiting for the response of the call insultMe that never got send

if __name__=='__ducky__':
    print("Starting servers in ", f"static({NUM_OF_NODES})" if (NUM_OF_NODES > 0) else "dynamic", " mode...")
    serverMng = spawnServers(NUM_OF_NODES)
    time.sleep(2)

    print("Starting Insult test... (making every worker(", NUM_OF_CLIENTS , ") do ", _REQS_PER_CLIENT, " reqs)")
    delta = time.time()
    spawnClients(num_clients=NUM_OF_CLIENTS, client_type=multiConnectClient, queue=INSULT_MANAGER_QUEUE ,method="insultMe", reps=_REQS_PER_CLIENT)
    waitForClients()
    delta = time.time() - delta
    
    print("Test finished.")
    reqs = NUM_OF_NODES*NUM_OF_CLIENTS*_REQS_PER_CLIENT
    print("RES: Made ", reqs, " reqs in ", delta, " secs. Got ", (reqs/delta), " reqs/s")

    print("Stoping the servers...")
    print("This: ", mp.current_process().pid, " | serverMng: ", serverMng.pid)
    serverMng.send_signal(signal.SIGTERM)
    time.sleep(5)
    try: serverMng.kill()
    except: pass
    print("Servers stopped.")