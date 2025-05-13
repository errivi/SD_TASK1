import threading
from xmlrpc.server import SimpleXMLRPCServer, SimpleXMLRPCRequestHandler
from xmlrpc.client import ServerProxy
import time
import re
import sys

# Server parameters
_INSULT_LIST_TTL = 60*5

if len(sys.argv) < 3:
    print("Using default values")
    insultServerURL = 'http://127.0.0.1:8000'
    filterServerPort = 9000
else:
    insultServerURL = sys.argv[1]
    filterServerPort = int(sys.argv[2])

addr_to_consume = ('127.0.0.1', filterServerPort)
addr_to_consume_as_str = f'http://{addr_to_consume[0]}:{addr_to_consume[1]}'

# Restrict to a particular path
class RequestHandler(SimpleXMLRPCRequestHandler):
    rpc_paths = ('/RPC2',)

# client for consuming InsultServer
insultService = ServerProxy(insultServerURL, allow_none=True)

# list for saving filtered text
filtered_text_results = []

# Regex to match the insults in the text
_pattern = None

# update function to update the insult list once a while
def update_insults(thread_abort_flag:threading.Event):
    global insults_set
    while not thread_abort_flag.is_set():
        try:
            global _pattern
            print(f"[Filter@{filterServerPort}] ➔ periodic update GET {insultServerURL}")
            insults_set = set(insultService.get())
            insults_list = sorted(insults_set, key=len, reverse=True)
            _pattern = re.compile(r'\b(' + '|'.join(re.escape(word) for word in insults_list) + r')\b', flags=re.IGNORECASE)
        except Exception as e:
            print(f"[Filter@{filterServerPort}] Error retrieving insults: {e}")
        thread_abort_flag.wait(timeout=_INSULT_LIST_TTL)

# periodic updates thread
thread_abort_flag = threading.Event()
threading.Thread(target=update_insults, args=(thread_abort_flag,), daemon=True).start()

# Create InsultFilter service
with SimpleXMLRPCServer(addr=addr_to_consume,
                        requestHandler=RequestHandler,
                        allow_none=True,
                        logRequests=False) as server:
    server.register_introspection_functions()

    # function that receives,filter, saves and returns the filtered text
    def filter_text(text):
        global _pattern
        # replace matching insults with 'CENSORED'
        filtered_version = _pattern.sub("CENSORED", text)
        # Store and return filtered text
        filtered_text_results.append(filtered_version)
        return filtered_version
    server.register_function(filter_text, 'filter')

    # function that return list of filtered texts
    def get_filtered_texts():
        return filtered_text_results
    server.register_function(get_filtered_texts, 'getFiltered')

    print("Filter service active on ", addr_to_consume_as_str)
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        print("Ending broadcast thread for subscribers...")
        thread_abort_flag.set()
        while threading.active_count() > 1: time.sleep(1)
        sys.exit(0)