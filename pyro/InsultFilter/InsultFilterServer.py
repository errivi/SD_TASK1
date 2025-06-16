import sys
import threading
import time
import re
import Pyro4

# Server parameters
_INSULT_LIST_TTL = 5 * 60  # 5 minutos
INSULT_SERVER_NAME = "example.InsultServer"

if len(sys.argv) < 2:
    print("[*] Using default filter port: 9000")
    filter_port = 9000
else:
    filter_port = int(sys.argv[1])


@Pyro4.expose
@Pyro4.behavior(instance_mode="single")
class InsultFilterServer:
    def __init__(self):
        self.insult_server_name = INSULT_SERVER_NAME
        self.pattern = re.compile("$")  # dummy
        self.results = []
        self.abort_flag = threading.Event()
        self.insult_proxy = None
        threading.Thread(target=self.update_insults, daemon=True).start()

    def update_insults(self):
        while not self.abort_flag.is_set():
            try:
                ns = Pyro4.locateNS()
                uri = ns.lookup(self.insult_server_name)
                proxy = Pyro4.Proxy(uri)

                print(f"[Filter] Updating insults from {self.insult_server_name}…")
                insults = proxy.get_insults()

                sorted_insults = sorted(insults, key=len, reverse=True)
                escaped = [re.escape(word) for word in sorted_insults]
                self.pattern = re.compile(r"\b(" + "|".join(escaped) + r")\b", flags=re.IGNORECASE)
            except Exception as e:
                print(f"[Filter] Error retrieving insults: {e}")
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
        print("[+] Name Server located.")
        uri = daemon.register(InsultFilterServer())
        ns.register("example.InsultFilterServer", uri)
    except Pyro4.errors.NamingError:
        print("[-] Couldn't register in Name Server, trying manual registration...")
        uri = daemon.register(InsultFilterServer(), objectId="example.InsultFilterServer")
    print(f"[+] FilterServer listening on port {filter_port} -> {uri}")
    try:
        daemon.requestLoop()
    except KeyboardInterrupt:
        print("[!] Shutting down filter server...")
        daemon.shutdown()
        sys.exit(0)