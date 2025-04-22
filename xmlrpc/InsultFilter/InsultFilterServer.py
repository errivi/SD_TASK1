import threading
from xmlrpc.server import SimpleXMLRPCServer
from xmlrpc.server import SimpleXMLRPCRequestHandler
from xmlrpc.client import ServerProxy
import random
import time

insults_set = set()

# Restrict to a particular path
class RequestHandler(SimpleXMLRPCRequestHandler):
    rpc_paths = ('/RPC2',)

# Create server
with SimpleXMLRPCServer(('localhost', 8000), requestHandler=RequestHandler, allow_none=True) as server:
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



    # Run the server's main loop
    print("Service server active on http://127.0.0.1:9000")
    server.serve_forever()
