import pika
import signal
import random
import sys

def _errorIncorrectArguments():
    print("Incorrect arguments were given! Script use: Insultmanager.py RabbitMQ_IP InultManagerQueueName")
    exit(-1)

_RABBITMQ_DIR = str(sys.argv[1]) if len(sys.argv) == 3 else _errorIncorrectArguments()
_INSULT_MANAGER_QUEUE = str(sys.argv[2]) if len(sys.argv) == 3 else _errorIncorrectArguments()

_insults = ["clown", "blockhead", "dimwit", "nincompoop", "simpleton", "dullard", "buffoon", "nitwit", "half-wit", "scatterbrain", "scatterbrained", "knucklehead", "dingbat", "doofus", "ninny", "ignoramus", "muttonhead", "bonehead", "airhead", "puddingbrain", "mushbrain", "blockhead", "dunderhead", "lamebrain", "muttonhead", "numbskull", "dimwit", "dullard", "fool", "goofball", "knucklehead", "lunkhead", "maroon", "mook", "nincompoop", "ninnyhammer", "numskull", "patzer", "puddingbrain", "sap", "simpleton", "scofflaw", "screwball", "twit", "woozle", "yahoo", "zany"]

def _startPikaConnection():
    connection_parameters = pika.ConnectionParameters(_RABBITMQ_DIR)
    connection = pika.BlockingConnection(connection_parameters)
    return (connection, connection.channel())

def InsultManager():
    def stopServer(signum, frame):
        channel.stop_consuming()
        connection.close()
        exit(0)

    signal.signal(signal.SIGINT, stopServer)
    signal.signal(signal.SIGTERM, stopServer)

    connection, channel = _startPikaConnection()
    channel.queue_declare(queue=_INSULT_MANAGER_QUEUE)

    def callback(ch, method, properties, body):
        import time
        startTS, beforeSendTS, afterSendTS = 0, 0, 0
        startTS = time.perf_counter()
        import pika
        def _returnResult(data):
            ch.basic_publish(
                exchange='',
                routing_key=str(properties.reply_to),
                properties=pika.BasicProperties(correlation_id=properties.correlation_id),
                body=data
            )
        args = body.decode()
        match properties.type:
            case 'add':
                try:
                    if args not in _insults: _insults.append(args)
                    _returnResult(data="Insult added successfully")
                except:
                    _returnResult(data="Insult could not be added")
            case 'get':
                _returnResult(data=str(_insults))
            case 'insultMe':
                i = 0
                for _ in range(100_000): i += 1 #Add latency to the request to mitigate not enough clients problem
                _returnResult(data=str(random.choice(list(_insults))) if len(_insults) > 0 else "NoInsultsSaved")
            case 'insultMeDEBUG':
                i = 0
                for _ in range(100_000): i += 1 #Add latency to the request to mitigate not enough clients problem
                beforeSendTS = time.perf_counter()
                _returnResult(data=str(random.choice(list(_insults))) if len(_insults) > 0 else "NoInsultsSaved")
                afterSendTS = time.perf_counter()
                print(f"{properties.type} -> StartTS: {startTS}, beforeSendTS: {beforeSendTS}, afterSendTS: {afterSendTS}, S-B: {beforeSendTS-startTS}, B-A: {afterSendTS-beforeSendTS}, S-A: {afterSendTS-startTS}")
            #case 'subscribe':
            #    pass # No need, to subscribe start consuming the fanout echange "subscription" as a client
            case _:
                print("ServMNG: Message was unknow. Ch: ", ch, " Method: ", method, " Properties: ", properties, " Body: ", body.decode())
                _returnResult(data="MethodNotKnow")
                pass
    
    #channel.basic_qos(prefetch_count=10)
    channel.basic_consume(queue=_INSULT_MANAGER_QUEUE, on_message_callback=callback, auto_ack=True)
    channel.start_consuming()

if __name__=='__main__':
    InsultManager()