import pika
import signal
import sys
import re

def _errorIncorrectArguments():
    print("Incorrect arguments were given! Script use: Insultmanager.py RabbitMQ_IP InultFilterQueueName")
    exit(-1)

_RABBITMQ_DIR = str(sys.argv[1]) if len(sys.argv) == 3 else _errorIncorrectArguments()
_INSULT_FILTER_QUEUE = str(sys.argv[2]) if len(sys.argv) == 3 else _errorIncorrectArguments()

_insults = ["clown", "blockhead", "dimwit", "nincompoop", "simpleton", "dullard", "buffoon", "nitwit", "half-wit", "scatterbrain", "scatterbrained", "knucklehead", "dingbat", "doofus", "ninny", "ignoramus", "muttonhead", "bonehead", "airhead", "puddingbrain", "mushbrain", "blockhead", "dunderhead", "lamebrain", "muttonhead", "numbskull", "dimwit", "dullard", "fool", "goofball", "knucklehead", "lunkhead", "maroon", "mook", "nincompoop", "ninnyhammer", "numskull", "patzer", "puddingbrain", "sap", "simpleton", "scofflaw", "screwball", "twit", "woozle", "yahoo", "zany"]

def _startPikaConnection():
    connection_parameters = pika.ConnectionParameters(_RABBITMQ_DIR)
    connection = pika.BlockingConnection(connection_parameters)
    return (connection, connection.channel())

def InsultFilter():
    def stopServer(signum, frame):
        channel.stop_consuming()
        connection.close()
        exit(0)

    signal.signal(signal.SIGINT, stopServer)
    signal.signal(signal.SIGTERM, stopServer)

    connection, channel = _startPikaConnection()
    channel.queue_declare(queue=_INSULT_FILTER_QUEUE)

    filtered_texts = []
    def callback(ch, method, properties, body):
        import pika
        def _returnResult(ch, properties, data):
            ch.basic_publish(
                exchange='',
                routing_key=str(properties.reply_to),
                properties=pika.BasicProperties(correlation_id=properties.correlation_id),
                body=data
            )
        _pattern = re.compile(r'\b(' + '|'.join(re.escape(word) for word in _insults) + r')\b', flags=re.IGNORECASE)
        args = body.decode()
        match properties.type:
            case 'filter':
                filtered = _pattern.sub("CENSORED", args)
                filtered_texts.append(filtered)
                _returnResult(ch, properties=properties, data=filtered)
            case 'getHistory':
                _returnResult(ch, properties=properties, data=str(filtered_texts))
            case _:
                print("ServMNG: Message was unknow. Ch: ", ch, " Method: ", method, " Properties: ", properties, " Body: ", body.decode())
                _returnResult(ch=ch, properties=properties, data="MethodNotKnow")
                pass
    
    channel.basic_consume(queue=_INSULT_FILTER_QUEUE, on_message_callback=callback, auto_ack=True)
    channel.start_consuming()

if __name__=='__main__':
    InsultFilter()