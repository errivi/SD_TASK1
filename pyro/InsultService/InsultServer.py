import sys
import threading
import time
import random
import Pyro4
from Pyro4.errors import NamingError

port = int(sys.argv[1])
insults_set = set()
subscribers_set = set()
subscribers_lock = threading.Lock()

@Pyro4.expose
@Pyro4.behavior(instance_mode="single")
class InsultServer(object):
    def add(self, insult):
        insults_set.add(insult)
        return True

    def get(self):
        return list(insults_set)

    def insult(self):
        if not insults_set:
            return None
        return random.choice(list(insults_set))

    def subscribe(self, subscriber_uri):
        with subscribers_lock:
            subscribers_set.add(subscriber_uri)
        return True

# Broadcaster thread
def broadcaster():
    while True:
        if insults_set and subscribers_set:
            insult = random.choice(list(insults_set))
            with subscribers_lock:
                for uri in list(subscribers_set):
                    try:
                        client = Pyro4.Proxy(uri)
                        client.receive_insult(insult)
                    except Exception as e:
                        print(f"Error sending to {uri}: {e}")
        time.sleep(5)


def main():
    # Start broadcaster thread
    threading.Thread(target=broadcaster, daemon=True).start()

    # Start Pyro daemon
    daemon = Pyro4.Daemon(host="localhost", port=port)
    try:
        ns = Pyro4.locateNS()
        uri = daemon.register(InsultServer)
        ns.register("example.insultserver", uri)
        print(f"InsultServer registered as 'example.insultserver' at {uri}")
    except NamingError:
        uri = daemon.register(InsultServer, objectId="example.insultserver")
        print(f"InsultServer available at {uri}")

    print(f"InsultServer listening on port {port}")
    daemon.requestLoop()

if __name__ == '__main__':
    main()