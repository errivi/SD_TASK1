import pika
import signal
import random
import sys

def _errorIncorrectArguments():
    print("Incorrect arguments were given! Script use: Insultmanager.py RabbitMQ_IP SubscriberExchangeName SubscriberQueueName")
    exit(-1)

_RABBITMQ_DIR = str(sys.argv[1]) if len(sys.argv) == 4 else _errorIncorrectArguments()
_SUBSCRIBER_EXCHANGE = str(sys.argv[2]) if len(sys.argv) == 4 else _errorIncorrectArguments()
_SUBSCRIBER_QUEUE = str(sys.argv[3]) if len(sys.argv) == 4 else _errorIncorrectArguments()

_insults = ["clown", "blockhead", "dimwit", "nincompoop", "simpleton", "dullard", "buffoon", "nitwit", "half-wit", "scatterbrain", "scatterbrained", "knucklehead", "dingbat", "doofus", "ninny", "ignoramus", "muttonhead", "bonehead", "airhead", "puddingbrain", "mushbrain", "blockhead", "dunderhead", "lamebrain", "muttonhead", "numbskull", "dimwit", "dullard", "fool", "goofball", "knucklehead", "lunkhead", "maroon", "mook", "nincompoop", "ninnyhammer", "numskull", "patzer", "puddingbrain", "sap", "simpleton", "scofflaw", "screwball", "twit", "woozle", "yahoo", "zany"]

def _startPikaConnection():
    connection_parameters = pika.ConnectionParameters(_RABBITMQ_DIR)
    connection = pika.BlockingConnection(connection_parameters)
    return (connection, connection.channel())

def InsultBroadcaster():
    def stopServer(signum, frame):
        connection.close()
        exit(0)

    signal.signal(signal.SIGINT, stopServer)
    signal.signal(signal.SIGTERM, stopServer)

    connection, channel = _startPikaConnection()
    channel.exchange_declare(exchange=_SUBSCRIBER_EXCHANGE, exchange_type='fanout')
    channel.queue_declare(queue=_SUBSCRIBER_QUEUE, durable=True, exclusive=True)
    channel.queue_bind(exchange=_SUBSCRIBER_EXCHANGE, queue=_SUBSCRIBER_QUEUE)

    while True:
        channel.basic_publish(
            exchange=_SUBSCRIBER_EXCHANGE,
            routing_key=_SUBSCRIBER_QUEUE,
            body=random.choice(list(_insults)) if len(_insults) > 0 else "NoInsultsSaved",
            properties=pika.BasicProperties(expiration="5005")
        )
        connection.sleep(5)

if __name__=='__main__':
    InsultBroadcaster()