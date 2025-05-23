from rapi import RabbitMQ_ClientAPI
import sys

# Configuration parameters
_RABBITMQ_DIR = '127.0.0.1'
_INSULT_MANAGER_QUEUE = 'insult_manager'
_INSULT_FILTER_QUEUE = 'insult_filter'
SUBSCRIBER_EXCHANGE = 'subscriber'
SUBSCRIBER_QUEUE = 'subscriber_broadcaster'

if __name__=='__main__':
    print("Starting connection to RabbitMQ...")
    rapi = RabbitMQ_ClientAPI(method_queue=_INSULT_MANAGER_QUEUE)
    rapi.connect()
    if rapi.connection.is_open: print("Connection started.")
    else:
        print("Could not start a connection to RabbitMQ, exiting...")
        sys.exit(-1)
    
    print("For technical reasons the insult list has entries already, starting list:")
    print(rapi.call("get"))
    print("Adding new insult to check add() method. Adding \"mequetrefe\" to the list...")
    rapi.call("add", "mequetrefe")
    print("Showing the new insult list with the new insult:")
    print(rapi.call("get"))

    for _ in range(5):
        print("Getting a random insult: ", rapi.call("get"))
    
    print("Starting subscription to the insult service...")
    rapi.subscribeTo(exchange_name=SUBSCRIBER_EXCHANGE, queue_name=SUBSCRIBER_QUEUE)