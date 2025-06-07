import sys
import subprocess as sp
import signal
import time

# Configuration parameters
RABBITMQ_DIR = '127.0.0.1'

INSULT_MANAGER_SCRIPT = 'InsultServer.py'
INSULT_MANAGER_QUEUE = 'insult_manager'

INSULT_FILTER_SCRIPT = 'InsultFilterServer.py'
INSULT_FILTER_QUEUE = 'insult_filter'

INSULT_BROADCASTER_SCRIPT = 'InsultBroadcaster.py'
SUBSCRIBER_EXCHANGE = 'subscriber'
SUBSCRIBER_QUEUE = 'subscriber_broadcaster'

# 0 for dynamic load balancing, >0 for static number of nodes
NUM_OF_NODES = int(sys.argv[1]) if int(sys.argv[1]) > 0 else 0

# Global variables
_managers = set()
_filters = set()
_broadcaster = set()

def startWorker(type:str):
    match type:
        case 'manager':
            p = sp.Popen([sys.executable, INSULT_MANAGER_SCRIPT, RABBITMQ_DIR, INSULT_MANAGER_QUEUE])
            _managers.add(p)
        case 'filter':
            p = sp.Popen([sys.executable, INSULT_FILTER_SCRIPT, RABBITMQ_DIR, INSULT_FILTER_QUEUE])
            _filters.add(p)
        case 'broadcaster':
            p = sp.Popen([sys.executable, INSULT_BROADCASTER_SCRIPT, RABBITMQ_DIR, SUBSCRIBER_EXCHANGE, SUBSCRIBER_QUEUE])
            _broadcaster.add(p)
        case _:
            print("WARNING: Tried creating unexisting type of worker, nothing will happen")

def initializeWorkers(num_manager:int, num_filter:int, broadcaster:bool):
    for _ in range(num_manager): startWorker('manager')
    for _ in range(num_filter): startWorker('filter')
    if broadcaster: startWorker('broadcaster')

def stopServers(signum, frame):
    print("ServMNG: Stop signal recieved, stoping the servers...")
    for worker in (_managers | _filters | _broadcaster):
        worker.terminate()
    print("ServMNG: All servers recieved termination order. Exiting now...")
    print("WARNING: This version of the script cannot ensure the workers processes get killed when called from another script, please manually close this terminal and start a new one to ensure proper clean-up (using \"start && exit\" should be enough), ignoring this step will result in unexpected behaviour")
    exit(0)

if __name__=='__main__':
    print("ServMNG: Starting initial nodes...")
    initializeWorkers(num_manager=NUM_OF_NODES, num_filter=NUM_OF_NODES, broadcaster=True)
    time.sleep(2)
    print("ServMNG: Initial nodes initialized! Now serving:")
    print("ServMNG: To stop the servers press Cntrl+C and wait around 5s")

    signal.signal(signal.SIGINT, stopServers)
    signal.signal(signal.SIGTERM, stopServers)
    signal.signal(signal.SIGBREAK, stopServers)

    while True: time.sleep(4)