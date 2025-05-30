import threading
from xmlrpc.server import SimpleXMLRPCServer, SimpleXMLRPCRequestHandler
from xmlrpc.client import ServerProxy
import random
import time
import sys


insults_set = set()
subscribers_set = set()
subscribers_lock = threading.Lock()
lost_subscribers = {}

if len(sys.argv) > 1: insultServerPort = int(sys.argv[1])
else: insultServerPort = 8000
addr_to_deploy = ('127.0.0.1', insultServerPort)
load_balancer_uri = 'http://127.0.0.1:7999'


# Method to remove a subscriber not only from the local list, but also from the load balancer's list copy
def remove_subscriber(subscriber_url):
    with subscribers_lock:
        subscribers_set.discard(subscriber_url)
    try:
        LB = ServerProxy(load_balancer_uri, allow_none=True)
        LB.unalive(subscriber_url)
        del LB
    except:
        pass

# Restrict to a particular path
class RequestHandler(SimpleXMLRPCRequestHandler):
    rpc_paths = ('/RPC2',)

# Create server
with SimpleXMLRPCServer(addr_to_deploy,
                        requestHandler=RequestHandler,
                        allow_none=True,
                        logRequests=False) as server:
    server.register_introspection_functions()

    def add_insult(insult):
        insults_set.add(insult)
        return True
    server.register_function(add_insult, 'add')

    def get_insults():
        return list(insults_set)
    server.register_function(get_insults, 'get')

    def insult_me():
        i = 0
        for _ in range(100_000): i += 1 #Add latency to the request to mitigate not enough clients problem
        if len(insults_set) == 0: return "NoInsultsSaved"
        else: return random.choice(list(insults_set))
    server.register_function(insult_me, 'insult')

    def subscribe_insults(subscriber_url):
        with subscribers_lock:
            subscribers_set.add(subscriber_url)
        return True
    server.register_function(subscribe_insults, 'subscribe') 

    def broadcaster(thread_abort_flag:threading.Event):
        while not thread_abort_flag.is_set():
            if insults_set and subscribers_set:
                insult = random.choice(list(insults_set))
                with subscribers_lock:
                    for url in subscribers_set:
                        try:
                            client = ServerProxy(url, allow_none=True)
                            client.receive_insult(insult)
                        except Exception as e:
                            print(f"Error while sending insult to client {url}: {e}")
                            if url not in lost_subscribers: lost_subscribers[url] = 1
                            else:
                                if lost_subscribers[url] > 1: remove_subscriber(url)
                                else: lost_subscribers[url] = lost_subscribers[url] + 1
            thread_abort_flag.wait(timeout=5)

    # periodic updates thread
    thread_abort_flag = threading.Event()
    threading.Thread(target=broadcaster,args=(thread_abort_flag,) ,  daemon=True).start()
    # Run the server's main loop
    print("Service server active on ", addr_to_deploy)
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        print("Ending broadcast thread for subscribers...")
        thread_abort_flag.set()
        while threading.active_count() > 1: time.sleep(1)
        sys.exit(0)