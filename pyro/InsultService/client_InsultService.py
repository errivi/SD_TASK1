import sys
import threading
import time
import Pyro4
from xmlrpc.client import ServerProxy

insult_server_uri = sys.argv[1]
callback_port = int(sys.argv[2])

# Callback handler
@Pyro4.expose
class CallbackHandler(object):
    def receive_insult(self, insult):
        print("New insult received:", insult)
        return True

# Start callback server
def start_callback_server():
    daemon = Pyro4.Daemon(host="localhost", port=callback_port)
    uri = daemon.register(CallbackHandler)
    try:
        ns = Pyro4.locateNS()
        ns.register(f"example.callback_{callback_port}", uri)
    except NamingError:
        pass
    print(f"Callback server listening at {uri}")
    daemon.requestLoop()

# Main client logic
def main():
    # Launch callback server in background
    threading.Thread(target=start_callback_server, daemon=True).start()
    time.sleep(1)  # wait for callback server up

    # Connect to InsultServer
    server = Pyro4.Proxy(insult_server_uri)

    # List available methods
    print("Methods on InsultServer:", server._pyroMethods)

    # Add insults
    server.add('tonto')
    server.add('cap de suro')

    # Get a random insult
    print("Random insult:", server.insult())

    # Get all insults
    print("Insults list:", server.get())

    # Subscribe to callbacks
    # Construct own URI
    callback_uri = f"PYRO:example.callback_{callback_port}@localhost:{callback_port}"
    server.subscribe(callback_uri)
    print("Subscribed with callback URI:", callback_uri)

    # Keep running to receive insults
    try:
        while True:
            time.sleep(1)
    except KeyboardInterrupt:
        print("Client shutting down.")

if __name__ == '__main__':
    main()
