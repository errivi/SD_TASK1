import threading
import time
from xmlrpc.server import SimpleXMLRPCServer, SimpleXMLRPCRequestHandler
from xmlrpc.client import ServerProxy
from multiprocessing import Process
import random

#DEBUGclass ClientRequestHandler(SimpleXMLRPCRequestHandler):
#DEBUG    rpc_paths = ('/RPC2',)
#DEBUG
#DEBUGdef receive_insult(insult):
#DEBUG    print("New insult received:", insult, "!")
#DEBUG    return True
#DEBUG
#DEBUGdef start_client_server(port):
#DEBUG    with SimpleXMLRPCServer(('127.0.0.1', port),
#DEBUG                            requestHandler=ClientRequestHandler,
#DEBUG                            allow_none=True) as client_server:
#DEBUG        client_server.register_introspection_functions()
#DEBUG        client_server.register_function(receive_insult, 'receive_insult')
#DEBUG        print("Client server active on http://127.0.0.1:{port}")
#DEBUG        client_server.serve_forever()
#DEBUG
#DEBUGthreading.Thread(target=start_client_server, daemon=True).start()

#DEBUG#client for consuming InsultServer
#DEBUGinsultServer = ServerProxy('http://127.0.0.1:7999', allow_none=True)
#DEBUG
#DEBUG# List available methods
#DEBUGprint("Available methods on InsultServer:", insultServer.system.listMethods())
#DEBUG
#DEBUG# List insults registered (should be empty)
#DEBUGprint("Server has now this insults: ", insultServer.get())
#DEBUG
#DEBUG# Add some insults
#DEBUGinsultServer.add('tonto')
#DEBUGinsultServer.add('cap de suro')
#DEBUG
#DEBUG# Obtain random insult
#DEBUGprint("Random insult:", insultServer.insult())
#DEBUG# Obtain insults list
#DEBUGprint("Insults list:", insultServer.get())
#DEBUG
#DEBUG# Subscribe for receiving periodic insults
#DEBUGprint("Subscribing to InsultServer...")
#DEBUGinsultServer.subscribe("http://127.0.0.1:9000")
#DEBUG
#DEBUG# Keep running to obtain insults from subscription
#DEBUGtry:
#DEBUG    while True:
#DEBUG        time.sleep(1)
#DEBUGexcept KeyboardInterrupt:
#DEBUG    print("Client ended.")

_workers = []
_NUM_GOBLINS = 1
BASE_GOBLIN_PORT = 10_000

def annoy(url, id):
    #reciever = f'http://127.0.0.1:{id}'
    #threading.Thread(target=start_client_server, args=(id), daemon=True).start()
    victim = ServerProxy(url, allow_none=True)
    #victim.subscribe(reciever)

    insults = ["clown", "blockhead", "dimwit", "nincompoop", "simpleton", "dullard", "buffoon", "nitwit", "half-wit", "scatterbrain", "scatterbrained", "knucklehead", "dingbat", "doofus", "ninny", "ignoramus", "muttonhead", "bonehead", "airhead", "puddingbrain", "mushbrain", "blockhead", "dunderhead", "lamebrain", "muttonhead", "numbskull", "dimwit", "dullard", "fool", "goofball", "knucklehead", "lunkhead", "maroon", "mook", "nincompoop", "ninnyhammer", "numskull", "patzer", "puddingbrain", "sap", "simpleton", "scofflaw", "screwball", "twit", "woozle", "yahoo", "zany"]
    while True:
        r = "none"; f = "none"
        match random.choice(("add", "get", "insult")):
            case "add":
                t = time.time()
                victim.add(random.choice(insults))
                t = time.time() - t
                f = "add"
            case "get":
                t = time.time()
                r = victim.get()
                t = time.time() - t
                f = "get"
            case "insult":
                t = time.time()
                r = victim.insult()
                t = time.time() - t
                f = "insult"
            case _:
                t = -1
                r = "none"
                f = "none"
        #print(id, ": ", t)
        #DEBUG|print(id, ": Did ", f, " and got ", r)

def reallyAnnoy(url, id):
    victim = ServerProxy(url, allow_none=True)
    while True:
        victim.insult()

def spawGoblins(func):
    for gob in range(_NUM_GOBLINS):
        p = Process(target=func, args=('http://127.0.0.1:7999', gob))
        _workers.append(p)
        p.start()

def metaAnnoy(id, a):
    insults = ["clown", "blockhead", "dimwit", "nincompoop", "simpleton", "dullard", "buffoon", "nitwit", "half-wit", "scatterbrain", "scatterbrained", "knucklehead", "dingbat", "doofus", "ninny", "ignoramus", "muttonhead", "bonehead", "airhead", "puddingbrain", "mushbrain", "blockhead", "dunderhead", "lamebrain", "muttonhead", "numbskull", "dimwit", "dullard", "fool", "goofball", "knucklehead", "lunkhead", "maroon", "mook", "nincompoop", "ninnyhammer", "numskull", "patzer", "puddingbrain", "sap", "simpleton", "scofflaw", "screwball", "twit", "woozle", "yahoo", "zany"]
    while True:
        port = random.choice((8000, 8001))
        victim = ServerProxy(f'http://127.0.0.1:{port}', allow_none=True)
        match random.choice(("add", "get", "insult")):
            case "add":
                t = time.time()
                victim.add(random.choice(insults))
                t = time.time() - t
            case "get":
                t = time.time()
                victim.get()
                t = time.time() - t
            case "insult":
                t = time.time()
                victim.insult()
                t = time.time() - t
            case _:
                t = -1
        print(time.time(), " - ", id, ": ", t)

def spawnMetaGoblins():
    for gob in range(_NUM_GOBLINS):
        p = Process(target=metaAnnoy, args=(gob, 1))
        _workers.append(p)
        p.start()

def killGoblins():
    for p in _workers:
        p.kill()

def floadServer():
    #spawGoblins(annoy)
    spawnMetaGoblins()
    time.sleep(3)
    killGoblins()

if __name__=='__main__':
    floadServer()