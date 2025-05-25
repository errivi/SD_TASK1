from rapi import RabbitMQ_ClientAPI

# Configuration parameters
RABBITMQ_DIR = '127.0.0.1'
INSULT_MANAGER_QUEUE = 'insult_manager'
SUBSCRIBER_EXCHANGE = 'subscriber'

if __name__=='__main__':
    print(" [*] Starting connection to RabbitMQ...")
    rapi = RabbitMQ_ClientAPI(host=RABBITMQ_DIR, method_queue=INSULT_MANAGER_QUEUE)
    
    print(" [!] For technical reasons the insult list has entries already, starting list:")
    print(rapi.call("get"))
    print(" [*] Adding new insult to check add() method. Adding \"mequetrefe\" to the list...")
    rapi.call("add", "mequetrefe")
    print(" [*] Showing the new insult list with the new insult:")
    print(rapi.call("get"))

    for _ in range(5):
        print(" [*] Getting a random insult: ", rapi.call("insultMe"))
    
    print(" [*] Starting subscription to the insult service...")
    rapi.subscribeTo(subscription_exchange=SUBSCRIBER_EXCHANGE)