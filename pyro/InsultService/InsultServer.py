import sys
import threading
import time
import random
import Pyro4


if len(sys.argv) > 1:
    insultServerPort = int(sys.argv[1])
else:
    insultServerPort = 8000
BASE_HOST = '127.0.0.1'
LOAD_BALANCER_URI = f"PYRO:LoadBalancer@{BASE_HOST}:7999"

@Pyro4.expose
@Pyro4.behavior(instance_mode="single")
class InsultServer:
    def __init__(self):
        self.insults_set = set()
        self.subscribers_set = set()
        self.lost_subscribers = {}
        self.lock = threading.Lock()
        self.abort_flag = threading.Event()
        # Start broadcast thread
        threading.Thread(target=self._broadcaster, daemon=True).start()

    def add_insult(self, insult):
        self.insults_set.add(insult)
        return True

    def get_insults(self):
        return list(self.insults_set)

    def insult_me(self):
        i = 0
        for _ in range(10_000): i += 1 #Add latency to the request to mitigate not enough clients problem
        if not self.insults_set: return "NoInsultsSaved"
        return random.choice(tuple(self.insults_set))

    def subscribe_insults(self, subscriber_uri):
        with self.lock:
            self.subscribers_set.add(subscriber_uri)
        return True

    def remove_subscriber(self, uri):
        with self.lock:
            self.subscribers_set.discard(uri)
        try:
            lb = Pyro4.Proxy(LOAD_BALANCER_URI)
            lb.unalive(uri)
        except:
            pass

    def _broadcaster(self):
        while not self.abort_flag.is_set():
            time.sleep(5)
            if self.insults_set and self.subscribers_set:
                insult = random.choice(tuple(self.insults_set))
                with self.lock:
                    for uri in list(self.subscribers_set):
                        try:
                            client = Pyro4.Proxy(uri)
                            client.receive_insult(insult)
                        except Exception as e:
                            print(f"Error while sending insult to client {uri}: {e}")
                            count = self.lost_subscribers.get(uri, 0) + 1
                            self.lost_subscribers[uri] = count
                            if count > 1:
                                self._remove_subscriber(uri)

if __name__ == '__main__':
    # Init Pyro daemon & register object
    daemon = Pyro4.Daemon(host=BASE_HOST, port=insultServerPort)
    try:
        ns = Pyro4.locateNS()
        uri = daemon.register(InsultServer)
        ns.register("example.InsultServer", uri)
        print(f"InsultServer registered in ns as example.InsultServer -> {uri}")
    except Pyro4.errors.NamingError:
        uri = daemon.register(InsultServer, objectId="example.InsultServer")
        print(f"InsultServer available at {uri}")

    print(f"InsultServer listening on {BASE_HOST}:{insultServerPort}")
    try:
        daemon.requestLoop()
    except KeyboardInterrupt:
        print("Stopping broadcaster & exiting...")
        server = daemon.objectsById.get("example.InsultServer")
        if server:
            server.abort_flag.set()
        daemon.shutdown()
        sys.exit(0)
