import threading
from xmlrpc.server import SimpleXMLRPCServer, SimpleXMLRPCRequestHandler
from xmlrpc.client import ServerProxy
import random
import time
import re
from sys import argv


insultServerURL = argv[1]
filterServerPort = int(argv[2])

# Restrict to a particular path
class RequestHandler(SimpleXMLRPCRequestHandler):
    rpc_paths = ('/RPC2',)

# client for consuming InsultServer
insultService = ServerProxy(insultServerURL, allow_none=True)
# Obtain initial insults list and print log
print(f"[Filter@{filterServerPort}] ➔ initial GET {insultServerURL}")
insults_set = set(insultService.get())

# list for saving filtered text
filtered_text_results = []

# update function to get most recent insults list
def update_insults():
    global insults_set
    while True:
        try:
            print(f"[Filter@{filterServerPort}] ➔ periodic update GET {insultServerURL}")
            insults_set = set(insultService.get())
        except Exception as e:
            print(f"[Filter@{filterServerPort}] Error retrieving insults: {e}")
        time.sleep(5)

# periodic updates thread
threading.Thread(target=update_insults, daemon=True).start()

# Create InsultFilter service
with SimpleXMLRPCServer(('localhost', filterServerPort), requestHandler=RequestHandler, allow_none=True) as server:
    server.register_introspection_functions()

    # function that receives,filter, saves and returns the filtered text
    def filter_text(text):
        # Order insults by length to avoid partial replacement
        insults_list = sorted(insults_set, key=len, reverse=True)
        # check if insults in text
        pattern = re.compile(r'\b(' + '|'.join(re.escape(word) for word in insults_list) + r')\b', flags=re.IGNORECASE)
        # replace matching insults with 'CENSORED'
        filtered_version = pattern.sub("CENSORED", text)
        # Store and return filtered text
        filtered_text_results.append(filtered_version)
        return filtered_version
    server.register_function(filter_text, 'filter')


    # function that return list of filtered texts
    def get_filtered_texts():
        return filtered_text_results
    server.register_function(get_filtered_texts, 'getFiltered')

    print("Filter service active on http://127.0.0.1:", filterServerPort)
    server.serve_forever()
