import sys
import multiprocessing as mp
import pika
import random
import signal
import time
import os

# Configuration parameters
_RABBITMQ_DIR = '127.0.0.1'
_INSULT_MANAGER_QUEUE = 'insult_manager'
_INSULT_FILTER_QUEUE = 'insult_filter'

# 0 for dynamic load balancing, >0 for static number of nodes
NUM_OF_NODES = int(sys.argv[1]) if int(sys.argv[1]) > 0 else 0
_insults = None

# Global variables
_managers = set()
_filters = set()

def returnResult(ch, method,  properties, data):
        ch.basic_publish(
            exchange='',
            routing_key=properties.reply_to,
            properties=pika.BasicProperties(correlation_id=properties.correlation_id),
            body=data
        )
        ch.basic_ack(delivery_tag=method.delivery_tag)

def InsultManager():
    def stopServer(signum, frame):
        exit(0)

    signal.signal(signal.SIGINT, stopServer)
    signal.signal(signal.SIGTERM, stopServer)

    channel = startPikaConnection()
    channel.queue_declare(queue=_INSULT_MANAGER_QUEUE)

    def callback(ch, method, properties, body):
        args = body.decode()
        match properties.type():
            case 'add':
                if args not in _insults: _insults.append(args)
            case 'get':
                returnResult(ch=ch, method=method, properties=properties, data=_insults)
            case 'insultMe':
                returnResult(ch=ch, method=method, properties=properties, data=random.choice(_insults))
            case 'subscribe':
                pass #TODO
            case _:
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
        args = body.decode()
        match properties.type():
            case 'filter':
                pass #TODO
            case 'getHistory':
                pass #TODO
            case _:
                pass
    
    channel.basic_consume(queue=_INSULT_MANAGER_QUEUE, on_message_callback=callback, auto_ack=True)
    channel.start_consuming()

def startPikaConnection():
    connection_parameters = pika.ConnectionParameters(_RABBITMQ_DIR)
    connection = pika.BlockingConnection(connection_parameters)
    return connection.channel()

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
        case _:
            print("WARNING: Tried creating unexisting type of worker, nothing will happen")

def initializeWorkers():
    startWorker('manager')
    #startWorker('filter')

def stopServers(signum, frame):
    print("ServMNG: Stop signal recieved, stoping the servers...")
    for worker in zip(_managers, _filters):
        os.kill(worker.pid, signal.SIGTERM)
    print("ServMNG: All servers recieved termination order. Exiting now...")
    #exit(0)

if __name__=='__main__':
    print("ServMNG: Starting initial nodes...")
    _insults = mp.Manager().list()
    initializeWorkers()
    time.sleep(2)
    print("ServMNG: Initial nodes initialized! Now serving:")

    for worker in zip(_managers, _filters): print("New worker: ", worker.pid)

    signal.signal(signal.SIGINT, stopServers)
    signal.signal(signal.SIGTERM, stopServers)

    #TODO: When message insultMe recieved server explodes