import sys
import threading
import time
import random
import Pyro4
from Pyro4.errors import NamingError

#las siguientes 4 lineas deberian ir dentro de insult server?
insultServerPort = int(sys.argv[1])
insults_set = set()
subscribers_set = set()
subscribers_lock = threading.Lock()
lost_subscribers = {}

@Pyro4.expose
@Pyro4.behavior(instance_mode="single")
class InsultServer(object):
    def add_insult(self, insult):
        insults_set.add(insult)
        return True

    def get_insult(self):
        return list(insults_set)

    def insult_me(self):
        if len(insults_set) == 0: return "NoInsultsSaved"
        else: return random.choice(list(insults_set))

    def subscribe_insults(self, subscriber_uri):
        with subscribers_lock:
            subscribers_set.add(subscriber_uri)
        return True

    def remove_subscriber(self, subscriber_uri):
        with self.lock:
            self.subscribers_set.discard(subscriber_uri)
        try:
            self.lb.unalive(subscriber_uri)
        except Exception as e:
            pass


# Broadcaster thread
def broadcaster():
    while True:
        if insults_set and subscribers_set:
            insult = random.choice(list(insults_set))
            with subscribers_lock:
                for uri in subscribers_set:
                    try:
                        client = Pyro4.Proxy(uri)
                        client.receive_insult(insult)
                        print(f"Error while sending insult to client {uri}: {e}")

                    except Exception as e:
                        print(f"Error while sending insult to client {uri}: {e}")
                        count = self.lost_subscribers.get(uri, 0) + 1
                        self.lost_subscribers[uri] = count
                        if count > 1:
                            self.remove_subscriber(uri)+ 1
        time.sleep(5)


def main():
    # Start broadcaster thread
    threading.Thread(target=broadcaster, daemon=True).start()

    # Start Pyro daemon
    daemon = Pyro4.Daemon(host="localhost", port=port)
    try:
        ns = Pyro4.locateNS()
        uri = daemon.register(InsultServer)
        ns.register("example.InsultServer", uri)
        print(f"InsultServer registered as 'example.InsultServer' at {uri}")
    except NamingError:
        uri = daemon.register(InsultServer, objectId="example.InsultServer")
        print(f"InsultServer available at {uri}")

    print(f"InsultServer listening on port {insultServerPort}")
    daemon.requestLoop()

if __name__ == '__main__':
    main()