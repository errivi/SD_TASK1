import threading
import time
from xmlrpc.server import SimpleXMLRPCServer, SimpleXMLRPCRequestHandler
from xmlrpc.client import ServerProxy

#client for consuming InsultFilterServer
insultFilterServer = ServerProxy('http://127.0.0.1:8000', allow_none=True)

# List available methods
print("Available methods on InsultFilterServer:", insultFilterServer.system.listMethods())

# Add some insults
insultFilterServer.add('tonto')
insultFilterServer.add('cap de suro')

# Obtain random insult
print("Random insult:", insultFilterServer.insult())
# Obtain insults list
print("Insults list:", insultFilterServer.get())


# Keep running to obtain insults from subscription
try:
    while True:
        time.sleep(1)
except KeyboardInterrupt:
    print("Client ended.")
