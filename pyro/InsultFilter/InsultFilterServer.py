import sys
import threading
import time
import re
import Pyro4

# Server parameters
_INSULT_LIST_TTL = 5 * 60  # 5 minutes

if len(sys.argv) < 3:
    print("Using default values")
    insult_server_uri = f"PYRO:example.InsultServer@127.0.0.1:8000"
    filter_port = 9000
else:
    insult_server_uri = sys.argv[1]
    filter_port = int(sys.argv[2])


@Pyro4.expose
@Pyro4.behavior(instance_mode="single")
class InsultFilterServer:
    def __init__(self, insult_uri):
        self.insult_uri = insult_uri
        self.pattern = re.compile("$")  # dummy
        self.results = []
        self.abort_flag = threading.Event()
        threading.Thread(target=self.update_insults, daemon=True).start()

    def update_insults(self):
        while not self.abort_flag.is_set():
            try:
                proxy = Pyro4.Proxy(self.insult_uri)
                print(f"[Filter @{self.insult_uri}] updating insults…")
                insults = proxy.get_insults()
                sorted_insults = sorted(insults, key=len, reverse=True)
                escaped = [re.escape(w) for w in sorted_insults]
                self.pattern = re.compile(r"\b(" + "|".join(escaped) + r")\b", flags=re.IGNORECASE)
            except Exception as e:
                print(f"[Filter@{self.insult_uri}] Error retrieving insults: {e}]")
            self.abort_flag.wait(timeout=_INSULT_LIST_TTL)

    def filter_text(self, text):
        filtered = self.pattern.sub("CENSORED", text)
        self.results.append(filtered)
        return filtered

    def get_filtered_texts(self):
        return list(self.results)

if __name__ == '__main__':
    daemon = Pyro4.Daemon(host="127.0.0.1", port=filter_port)
    try:
        ns = Pyro4.locateNS()
        uri = daemon.register(InsultFilterServer(insult_server_uri))
        ns.register("example.InsultFilterServer", uri)
    except Pyro4.errors.NamingError:
        uri = daemon.register(InsultFilterServer(insult_server_uri), objectId="example.InsultFilterServer")
    print(f"FilterServer listening on port {filter_port} -> {uri}")
    try:
        daemon.requestLoop()
    except KeyboardInterrupt:
        print("Ending broadcast thread for subscribers...")
        InsultFilterServer.abort_flag.set()
        daemon.shutdown()
        sys.exit(0)
