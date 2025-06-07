import time
import sys
import subprocess as sp
import multiprocessing as mp
import signal
from rapi import RabbitMQ_ClientAPI
import os

## Configuration parameters trough arguments
# 0 for dynamic load balancing, >0 for static number of nodes
NUM_OF_NODES = int(sys.argv[1]) if len(sys.argv) > 1 and int(sys.argv[1]) > 0 else 0

## Hard configuration parameters
INSULT_MANAGER_QUEUE = 'insult_manager'
INSULT_FILTER_QUEUE = 'insult_filter'

# Client test configuration
TOTAL_NUM_REQS = 5_000
NUM_OF_CLIENTS = 6
_REQS_PER_CLIENT = int(TOTAL_NUM_REQS / (NUM_OF_CLIENTS))

# Fload test configuration
FLOAD_NUM_REQS = 1_000_000
NUM_OF_FLOADERS = 5
_REQS_PER_FLOADER = int(FLOAD_NUM_REQS / (NUM_OF_FLOADERS))

# Timing test configuration
N_REQUESTS_TO_TIME = 1_000
N_REQS_TO_APROXIMATE = 5_000

# Call method profiling configuration
VERBOSE_PROFILING = True
N_PROFILE_METHOD_CALLS = 3

## Global variables
_clients = []
_flooders = []

def spawnServers(num_nodes:int):
    p = sp.Popen([sys.executable, "ServerManager.py", str(num_nodes)],
                 #stdout=sp.PIPE,
                 #stderr=sp.PIPE,
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
    rapi.flood(reps=reps, method_name=method, replyTo="floadTest")

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

def timingTest():
    print("Starting servers in ", f"static({NUM_OF_NODES})" if (NUM_OF_NODES > 0) else "dynamic", " mode...")
    serverMng = spawnServers(NUM_OF_NODES)
    time.sleep(5)

    print(f"Making {N_REQUESTS_TO_TIME} requests and measuring their average time-to-response:")
    rapi = RabbitMQ_ClientAPI(method_queue=INSULT_MANAGER_QUEUE)
    insult = None
    total_delta = 0
    for _ in range(N_REQUESTS_TO_TIME):
        delta = time.perf_counter()
        insult = rapi.call("insultMe")
        delta = time.perf_counter() - delta
        total_delta += delta
    speed = total_delta/N_REQUESTS_TO_TIME
    print(f"Got an average of {speed} seconds per request, so {N_REQS_TO_APROXIMATE} would complete in {N_REQS_TO_APROXIMATE*speed}s and the average was {1/speed} reqs/s")
    print("Last insult was: ", insult)

    print("Stoping the servers...")
    print("Ports used for -> This: ", mp.current_process().pid, " | serverMng: ", serverMng.pid)
    os.kill(serverMng.pid, signal.CTRL_BREAK_EVENT)
    os.kill(serverMng.pid, signal.SIGTERM)
    serverMng.send_signal(signal.SIGTERM)
    time.sleep(5)
    try: serverMng.terminate()
    except: pass
    print("Servers stopped.")

def callProfiling():
    print("Starting servers in ", f"static({NUM_OF_NODES})" if (NUM_OF_NODES > 0) else "dynamic", " mode...")
    serverMng = spawnServers(NUM_OF_NODES)
    time.sleep(5)

    print(f"Making {N_PROFILE_METHOD_CALLS} requests and measuring their average time-to-response:")
    rapi = RabbitMQ_ClientAPI(method_queue=INSULT_MANAGER_QUEUE)
    total_delta, total_real_delta, total_wait, total_wait_iter = 0, 0, 0, 0
    for _ in range(N_PROFILE_METHOD_CALLS):
        delta = time.perf_counter()
        print("Call made at ", time.perf_counter())
        (start, send, wait, wait_n, finish, response) = rapi.callDEBUG("insultMeDEBUG")
        print("Call returned at: ", time.perf_counter())
        delta = time.perf_counter() - delta
        start_to_send = send - start
        send_to_wait = wait - send
        start_to_wait = wait - start
        start_to_finish = finish - start
        miscelaneous = delta - start_to_finish
        total_wait += send_to_wait
        total_wait_iter += wait_n
        total_real_delta += start_to_finish
        total_delta += delta
        if(VERBOSE_PROFILING): print(f"New request in seconds:\n\tdelta: {delta}\n\tmiscel: {miscelaneous}\n\treal: {start_to_finish}\n\tS-s: {start_to_send}\n\ts-w: {send_to_wait}\n\tS-w: {start_to_wait}\n\tNumWaits: {wait_n}\n\tResponse: {response}")
    speed = total_delta/N_PROFILE_METHOD_CALLS
    real_speed = total_real_delta/N_PROFILE_METHOD_CALLS
    print(f"API method average execution time: {real_speed} calls/s")
    print(f"Average response waiting time: {total_wait/N_PROFILE_METHOD_CALLS} made in an average of {total_wait_iter/N_PROFILE_METHOD_CALLS} iterations")
    print(f"Got an average of {speed} seconds per request or {1/speed} reqs/s")

    print("Stoping the servers...")
    print("Ports used for -> This: ", mp.current_process().pid, " | serverMng: ", serverMng.pid)
    os.kill(serverMng.pid, signal.CTRL_BREAK_EVENT)
    os.kill(serverMng.pid, signal.SIGTERM)
    serverMng.send_signal(signal.SIGTERM)
    time.sleep(5)
    try: serverMng.terminate()
    except: pass
    print("Servers stopped.")

def floadTest():
    print("This test is  NOT AUTOMATIC, it's intended use is making it easy to debug speed issues by floading the work queue, but it's YOUR WORK to empty it")
    print("Flooding the server with ", FLOAD_NUM_REQS, " \"insultMe\" reqs (", NUM_OF_FLOADERS, "w x ", _REQS_PER_FLOADER, "reqs each) to measure how long it takes to empty...")
    spawnFloaders(num_clients=NUM_OF_FLOADERS, queue=INSULT_MANAGER_QUEUE ,method="insultMe", reps=_REQS_PER_FLOADER)
    waitForFloader()

    rapi = RabbitMQ_ClientAPI(method_queue=INSULT_MANAGER_QUEUE)
    q = rapi.channel.queue_declare(queue=INSULT_MANAGER_QUEUE).method
    reqs = q.message_count
    print("Filled work queue with ", reqs, "reqs (test starts in 5 s)")
    print("Remember: Test isn't over, you have to execute ServerManager.py and check RabbitMQ's GUI to debug any speed trouble you're having or purge the queue to reset it's state")

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
    os.kill(serverMng.pid, signal.CTRL_BREAK_EVENT)
    os.kill(serverMng.pid, signal.SIGTERM)
    serverMng.send_signal(signal.SIGTERM)
    time.sleep(5)
    try: serverMng.terminate()
    except: pass
    print("Servers stopped.")

if __name__=='__main__':
    clientTest()