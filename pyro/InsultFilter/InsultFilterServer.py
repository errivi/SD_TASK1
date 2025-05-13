#!/usr/bin/env python3
import sys
import threading
import time
import re
import Pyro4


insult_server_uri = sys.argv[1]
filter_server_port = int(sys.argv[2])

# Create Pyro4 proxy to consume InsultServer
insult_service = Pyro4.Proxy(insult_server_uri)
# Obtain initial insults list
print(f"[Filter@{filter_server_port}] ➔ initial GET {insult_server_uri}")
insults_set = set(insult_service.get())

# List for saving filtered text
filtered_text_results = []

# Function to periodically update insults set
def update_insults():
    global insults_set
    while True:
        try:
            print(f"[Filter@{filter_server_port}] ➔ periodic update GET {insult_server_uri}")
            insults_set = set(insult_service.get())
        except Exception as e:
            print(f"[Filter@{filter_server_port}] Error retrieving insults list: {e}")
        time.sleep(5)

# periodic updates thread
threading.Thread(target=update_insults, daemon=True).start()

@Pyro4.expose
@Pyro4.behavior(instance_mode="single")
class InsultFilter(object):

    def filter_text(self, text):
        # Order insults by length to avoid partial replacements
        insults_list = sorted(insults_set, key=len, reverse=True)
        # check if insults in text
        pattern = re.compile(r'\b(' + '|'.join(re.escape(word) for word in insults_list) + r')\b',flags=re.IGNORECASE)
        # replace matching insults with 'CENSORED'
        filtered_version = pattern.sub('CENSORED', text)
        # Store and return filtered text
        filtered_text_results.append(filtered_version)
        return filtered_version

    def get_filtered_texts(self):
        return filtered_text_results


def main():
    # Initialize Pyro4 Daemon
    daemon = Pyro4.Daemon(host="localhost", port=filter_server_port)
    try:
        # Try to register with Name Server
        ns = Pyro4.locateNS()
        uri = daemon.register(InsultFilter)
        ns.register("example.InsultFilter", uri)
        print(f"InsultFilter registered as 'example.InsultFilter' at {uri}")
    except Pyro4.errors.NamingError:
        # Name server not found, register anonymously
        uri = daemon.register(InsultFilter, objectId="example.InsultFilter")
        print(f"InsultFilter service available at {uri}")

    print(f"Filter service listening on port {filter_server_port}")
    daemon.requestLoop()

if __name__ == '__main__':
    main()
