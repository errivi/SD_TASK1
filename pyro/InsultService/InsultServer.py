import sys
import threading
import time
import random
import Pyro4

# Usage: python InsultServer.py [port]
if len(sys.argv) > 1:
    insultServerPort = int(sys.argv[1])
else:
    insultServerPort = 8000
BASE_HOST = '127.0.0.1'

@Pyro4.expose
@Pyro4.behavior(instance_mode="single")
class InsultServer:
    def __init__(self):
        self.insults_set = set()
        self.subscribers_set = set()
        self.lost_subscribers = {}
        self.lock = threading.Lock()
        self.abort_flag = threading.Event()
        threading.Thread(target=self._broadcaster, daemon=True).start()

    def add_insult(self, insult):
        self.insults_set.add(insult)
        return True

    def get_insults(self):
        return list(self.insults_set)

    def insult_me(self):
        # Latencia artificial
        i = 0
        for _ in range(100_000): i += 1
        if not self.insults_set:
            return "NoInsultsSaved"
        return random.choice(tuple(self.insults_set))

    def subscribe_insults(self, subscriber_uri):
        with self.lock:
            self.subscribers_set.add(subscriber_uri)
        return True

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
                                self.remove_subscriber(uri)

if __name__ == '__main__':
    daemon = Pyro4.Daemon(host=BASE_HOST, port=insultServerPort)
    # Intentar localizar Name Server; si falla, salimos.
    try:
        ns = Pyro4.locateNS()
    except Exception as e:
        print(f"ERROR: No se pudo localizar el Name Server: {e}")
        sys.exit(1)

    # Registrar el servidor en el Name Server bajo un nombre con el puerto
    server = InsultServer()
    objectId = "example.InsultServer"
    uri = daemon.register(server, objectId=objectId)
    try:
        ns.register(objectId, uri)
        print(f"InsultServer registrado en NS como {objectId} -> {uri}")
    except Exception as e:
        print(f"ERROR: No se pudo registrar en el Name Server: {e}")
        sys.exit(1)

    print(f"InsultServer listening on {BASE_HOST}:{insultServerPort}")
    try:
        daemon.requestLoop()
    except KeyboardInterrupt:
        print("Stopping broadcaster & exiting...")
        server.abort_flag.set()
        daemon.shutdown()
        sys.exit(0)