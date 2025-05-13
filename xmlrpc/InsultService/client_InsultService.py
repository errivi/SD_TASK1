import threading
import time
from xmlrpc.server import SimpleXMLRPCServer, SimpleXMLRPCRequestHandler
from xmlrpc.client import ServerProxy

addr_to_recieve = ('127.0.0.1', 8999)
addr_to_recieve_as_str = f'http://{addr_to_recieve[0]}:{addr_to_recieve[1]}'
addr_to_consume = "http://127.0.0.1:8000"

class ClientRequestHandler(SimpleXMLRPCRequestHandler):
    rpc_paths = ('/RPC2',)

def receive_insult(insult):
    print("New insult received:", insult, "!")
    return True

def start_client_server():
    with SimpleXMLRPCServer(addr_to_recieve,
                            requestHandler=ClientRequestHandler,
                            logRequests=False,
                            allow_none=True) as client_server:
        client_server.register_introspection_functions()
        client_server.register_function(receive_insult, 'receive_insult')
        print("Client server active on ", addr_to_recieve)
        client_server.serve_forever()

threading.Thread(target=start_client_server, daemon=True).start()

# client for consuming InsultServer
insultServer = ServerProxy(uri=addr_to_consume, allow_none=True)

# List available methods
print("Available methods on InsultServer:", insultServer.system.listMethods())

# List insults registered (should be empty)
print("Server has now this insults: ", insultServer.get())

# Add some insults
print("Filling the server with insults...")
insults = ['tarzan de maceta', 'chichon de suelo', 'duende', 'pitufo', 'media pulga', 'inspector de baldosas', 'leñador de bonsais']
for insult in insults: insultServer.add(insult)

# Obtain insults list
print("Insults list:", insultServer.get())

# Obtain random insult
print("Random insult:", insultServer.insult())

# Subscribe for receiving periodic insults
print("Subscribing to InsultServer...")
insultServer.subscribe(addr_to_recieve_as_str)

# Keep running to obtain insults from subscription
try:
    while True:
        time.sleep(1)
except KeyboardInterrupt:
    print("Client ended.")