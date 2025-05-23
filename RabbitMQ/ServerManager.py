import sys
import multiprocessing as mp
import pika
import random
import signal
import time
import os
import re

# Configuration parameters
_RABBITMQ_DIR = '127.0.0.1'
_INSULT_MANAGER_QUEUE = 'insult_manager'
_INSULT_FILTER_QUEUE = 'insult_filter'
SUBSCRIBER_EXCHANGE = 'subscriber'
SUBSCRIBER_QUEUE = 'subscriber_broadcaster'

# 0 for dynamic load balancing, >0 for static number of nodes
NUM_OF_NODES = int(sys.argv[1]) if int(sys.argv[1]) > 0 else 0
_insults = ["clown", "blockhead", "dimwit", "nincompoop", "simpleton", "dullard", "buffoon", "nitwit", "half-wit", "scatterbrain", "scatterbrained", "knucklehead", "dingbat", "doofus", "ninny", "ignoramus", "muttonhead", "bonehead", "airhead", "puddingbrain", "mushbrain", "blockhead", "dunderhead", "lamebrain", "muttonhead", "numbskull", "dimwit", "dullard", "fool", "goofball", "knucklehead", "lunkhead", "maroon", "mook", "nincompoop", "ninnyhammer", "numskull", "patzer", "puddingbrain", "sap", "simpleton", "scofflaw", "screwball", "twit", "woozle", "yahoo", "zany"]

# Global variables
_managers = set()
_filters = set()
_broadcaster = set()

def startPikaConnection():
    connection_parameters = pika.ConnectionParameters(_RABBITMQ_DIR)
    connection = pika.BlockingConnection(connection_parameters)
    return connection.channel()

def returnResult(properties, data):
        channel = startPikaConnection()
        channel.basic_publish(
            exchange='',
            routing_key=str(properties.reply_to),
            properties=pika.BasicProperties(correlation_id=properties.correlation_id),
            body=data
        )

def InsultManager():
    def stopServer(signum, frame):
        exit(0)

    signal.signal(signal.SIGINT, stopServer)
    signal.signal(signal.SIGTERM, stopServer)

    channel = startPikaConnection()
    channel.queue_declare(queue=_INSULT_MANAGER_QUEUE)

    def callback(ch, method, properties, body):
        args = body.decode()
        match properties.type:
            case 'add':
                print("Zi me llego el add ", args)
                if args not in _insults: _insults.append(args)
            case 'get':
                print("Zi me llego el get")
                ch.basic_publish(
                    exchange='',
                    routing_key=str(properties.reply_to),
                    properties=pika.BasicProperties(correlation_id=properties.correlation_id),
                    body=str(_insults)
                )
                #returnResult(properties=properties, data=_insults)
            case 'insultMe':
                print("Zi me llego el insultMe")
                #insult = random.choice(list(_insults)) if len(_insults) > 0 else "NoInsultsSaved"
                #insult = insult
                #ch.basic_ack(delivery_tag=method.delivery_tag)
                #print("Requested insult, got: ", insult)
                ch.basic_publish(
                    exchange='',
                    routing_key=str(properties.reply_to),
                    properties=pika.BasicProperties(correlation_id=properties.correlation_id),
                    body=random.choice(list(_insults)) if len(_insults) > 0 else "NoInsultsSaved"
                )
                #returnResult(properties=properties, data=random.choice(list(_insults)) if len(_insults) > 0 else "NoInsultsSaved")
            #case 'subscribe':
            #    pass # No need, to subscribe start consuming the fanout echange "subscription" as a client
            case _:
                print("ServMNG: Message was unknow. Ch: ", ch, " Method: ", method, " Properties: ", properties, " Body: ", body.decode())
                pass
    
    channel.basic_consume(queue=_INSULT_MANAGER_QUEUE, on_message_callback=callback, auto_ack=True)
    channel.start_consuming()

def InsultFilter():
    def stopServer(signum, frame):
        exit(0)

    signal.signal(signal.SIGINT, stopServer)
    signal.signal(signal.SIGTERM, stopServer)

    channel = startPikaConnection()
    channel.queue_declare(queue=_INSULT_FILTER_QUEUE)

    def callback(ch, method, properties, body):
        _pattern = re.compile(r'\b(' + '|'.join(re.escape(word) for word in _insults) + r')\b', flags=re.IGNORECASE)
        filtered_texts = []
        args = body.decode()
        match properties.type:
            case 'filter':
                filtered = _pattern.sub("CENSORED", args)
                filtered_texts.append(filtered)
                returnResult(properties=properties, data=filtered)
            case 'getHistory':
                returnResult(properties=properties, data=filtered_texts)
            case _:
                pass
    
    channel.basic_consume(queue=_INSULT_FILTER_QUEUE, on_message_callback=callback, auto_ack=True)
    channel.start_consuming()

def InsultBroadcaster():
    def stopServer(signum, frame):
        exit(0)

    signal.signal(signal.SIGINT, stopServer)
    signal.signal(signal.SIGTERM, stopServer)

    channel = startPikaConnection()
    channel.exchange_declare(exchange=SUBSCRIBER_EXCHANGE, exchange_type='fanout')
    channel.queue_declare(queue=SUBSCRIBER_QUEUE, durable=True, exclusive=True)
    channel.queue_bind(exchange=SUBSCRIBER_EXCHANGE, queue=SUBSCRIBER_QUEUE)

    while True:
        channel.basic_publish(
            exchange=SUBSCRIBER_EXCHANGE,
            routing_key=SUBSCRIBER_QUEUE,
            body=random.choice(list(_insults)) if len(_insults) > 0 else "NoInsultsSaved",
            properties=pika.BasicProperties(expiration="5100")
        )
        time.sleep(5)

def startWorker(type:str):
    match type:
        case 'manager':
            p = mp.Process(target=InsultManager)
            _managers.add(p)
            p.start()
        case 'filter':
            p = mp.Process(target=InsultFilter)
            _filters.add(p)
            p.start()
        case 'broadcaster':
            p = mp.Process(target=InsultBroadcaster)
            _broadcaster.add(p)
            p.start()
        case _:
            print("WARNING: Tried creating unexisting type of worker, nothing will happen")

def initializeWorkers(num_manager:int, num_filter:int, broadcaster:bool):
    for _ in range(num_manager): startWorker('manager')
    for _ in range(num_filter): startWorker('filter')
    if broadcaster: startWorker('broadcaster')

def stopServers(signum, frame):
    print("ServMNG: Stop signal recieved, stoping the servers...")
    for worker in zip(_managers, _filters):
        os.kill(worker.pid, signal.SIGTERM)
    os.kill(_broadcaster.pop().pid, signal.SIGTERM)
    print("ServMNG: All servers recieved termination order. Exiting now...")
    #exit(0)

if __name__=='__main__':
    print("ServMNG: Starting initial nodes...")
    _insults = mp.Manager().list()
    initializeWorkers(1, 1, True)
    time.sleep(2)
    print("ServMNG: Initial nodes initialized! Now serving:")

    signal.signal(signal.SIGINT, stopServers)
    signal.signal(signal.SIGTERM, stopServers)