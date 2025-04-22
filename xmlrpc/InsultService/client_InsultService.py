import threading
import time
from xmlrpc.server import SimpleXMLRPCServer, SimpleXMLRPCRequestHandler
from xmlrpc.client import ServerProxy


class ClientRequestHandler(SimpleXMLRPCRequestHandler):
    rpc_paths = ('/RPC2',)

def receive_insult(insult):
    print("New insult received:", insult, "!")
    return True

def start_client_server():
    with SimpleXMLRPCServer(('127.0.0.1', 9000),
                            requestHandler=ClientRequestHandler,
                            allow_none=True) as client_server:
        client_server.register_introspection_functions()
        client_server.register_function(receive_insult, 'receive_insult')
        print("Client server active on http://127.0.0.1:9000")
        client_server.serve_forever()

threading.Thread(target=start_client_server, daemon=True).start()

#client for consuming InsultServer
insultServer = ServerProxy('http://127.0.0.1:8000', allow_none=True)

# List available methods
print("Available methods on InsultServer:", insultServer.system.listMethods())

# Add some insults
insultServer.add('tonto')
insultServer.add('cap de suro')

# Obtain random insult
print("Random insult:", insultServer.insult())
# Obtain insults list
print("Insults list:", insultServer.get())

# Subscribe for receiving periodic insults
print("Subscribing to InsultServer...")
insultServer.subscribe("http://127.0.0.1:9000")

# Keep running to obtain insults from subscription
try:
    while True:
        time.sleep(1)
except KeyboardInterrupt:
    print("Client ended.")
