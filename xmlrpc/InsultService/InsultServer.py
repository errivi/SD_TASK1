import threading
from xmlrpc.server import SimpleXMLRPCServer
from xmlrpc.server import SimpleXMLRPCRequestHandler
from xmlrpc.client import ServerProxy
import random
import time
from sys import argv


insults_set = set()
subscribers_set = set()
subscribers_lock = threading.Lock()
insultServerPort = int(argv[1])

# Restrict to a particular path
class RequestHandler(SimpleXMLRPCRequestHandler):
    rpc_paths = ('/RPC2',)

# Create server
with SimpleXMLRPCServer(('localhost', int(argv[1])), requestHandler=RequestHandler, allow_none=True) as server:
    server.register_introspection_functions()

    def add_insult(insult):
        insults_set.add(insult)
        return True
    server.register_function(add_insult, 'add')

    def get_insults():
        return list(insults_set)
    server.register_function(get_insults, 'get')

    def insult_me():
        return random.choice(list(insults_set))
    server.register_function(insult_me, 'insult')

    def subscribe_insults(subscriber_url):
        with subscribers_lock:
            subscribers_set.add(subscriber_url)
        return True
    server.register_function(subscribe_insults, 'subscribe')

    def broadcaster():
        while True:
            if insults_set and subscribers_set:
                insult = random.choice(list(insults_set))
                with subscribers_lock:
                    for url in subscribers_set:
                        try:
                            client = ServerProxy(url, allow_none=True)
                            client.receive_insult(insult)
                        except Exception as e:
                            print(f"Error while sending insult to client {url}: {e}")
            time.sleep(5)

    # periodic updates thread
    threading.Thread(target=broadcaster, daemon=True).start()
    # Run the server's main loop
    print("Service server active on http://127.0.0.1:",insultServerPort)
    server.serve_forever()
