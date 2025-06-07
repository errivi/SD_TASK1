import pika
import uuid
import time

class RabbitMQ_ClientAPI(object):
    def __init__(self, method_queue, host='127.0.0.1', port=5672, username='guest', password='guest', virtual_host='/', heartbeat=60):
        self.connection_params = pika.ConnectionParameters(
            host=host,
            port=port,
            virtual_host=virtual_host,
            credentials=pika.PlainCredentials(username, password),
            heartbeat=heartbeat
        )
        self.connection = pika.BlockingConnection(self.connection_params)
        self.channel = self.connection.channel()

        self.method_queue = method_queue
        self.corr_id = str(uuid.uuid4())
        self.callback_queue = self.corr_id
        self.channel.queue_declare(
            queue=self.callback_queue,
            durable=False,
            auto_delete=True,
            exclusive=True)

        self.basic_tag = self.channel.basic_consume(
            queue=self.callback_queue,
            on_message_callback=self.on_response,
            auto_ack=True)

        self.response = None

    def on_response(self, ch, method, props, body):
        if self.corr_id == props.correlation_id:
            self.response = body.decode()
    
    def on_notification(self, ch, method, props, body):
        self.response = body.decode()

    def call(self, method_name:str, args:str=""):
        self.response = None
        self.channel.basic_publish(
            exchange='',
            routing_key=self.method_queue,
            properties=pika.BasicProperties(reply_to=self.callback_queue, correlation_id=self.corr_id, type=method_name),
            body=args)
        while self.response is None:
            self.connection.process_data_events(time_limit=1)
        return self.response
    
    def callDEBUG(self, method_name:str, args:str=""):
        start, send, wait = None, None, None
        wait_n = 0
        start = time.perf_counter()
        self.response = None
        self.channel.basic_publish(
            exchange='',
            routing_key=self.method_queue,
            properties=pika.BasicProperties(reply_to=self.callback_queue, correlation_id=self.corr_id, type=method_name),
            body=args)
        send = time.perf_counter()
        while self.response is None:
            #time.sleep(0.005)
            #self.connection.sleep(0.0001)
            self.connection.process_data_events(time_limit=1)
            wait = time.perf_counter()
            wait_n += 1
        return (start, send, wait, wait_n, time.perf_counter(), self.response)
    
    def flood(self, reps:int, replyTo:str, method_name:str, args:str=""):
        self.channel.basic_cancel(consumer_tag=self.basic_tag)
        self.channel.queue_declare(queue=replyTo)

        props = pika.BasicProperties(reply_to=replyTo, correlation_id=self.corr_id, type=method_name)
        for _ in range(reps):
            self.channel.basic_publish(
                exchange='',
                routing_key=self.method_queue,
                properties=props,
                body=args)

        self.channel.queue_declare(queue=self.callback_queue, durable=False, auto_delete=True, exclusive=True)
        self.basic_tag = self.channel.basic_consume(queue=self.callback_queue, on_message_callback=self.on_response, auto_ack=True)

    def subscribeTo(self, subscription_exchange:str):
        self.channel.basic_cancel(consumer_tag=self.basic_tag)
        self.channel.queue_declare(queue=self.callback_queue, durable=False, auto_delete=True, exclusive=True)

        self.channel.exchange_declare(exchange=subscription_exchange, exchange_type='fanout')
        self.channel.queue_bind(exchange=subscription_exchange, queue=self.callback_queue)

        consumer_tag = self.channel.basic_consume(queue=self.callback_queue, on_message_callback=self.on_notification, auto_ack=True)
        try:
            print(" [!] Press Cntrl+C to cancel subscription: ")
            delta = time.time() - 4.75
            while True:
                if (time.time() - delta) > 4.75:
                    if self.response: print("[", time.ctime(time.time()), "] -> Got insult: ", self.response)
                delta = time.time()
                self.connection.process_data_events(time_limit=5)
        except KeyboardInterrupt: pass
        finally:
            self.channel.basic_cancel(consumer_tag=consumer_tag)
            self.channel.queue_unbind(exchange=subscription_exchange, queue=self.callback_queue)

            self.channel.queue_declare(queue=self.callback_queue, durable=False, auto_delete=True, exclusive=True)
            self.basic_tag = self.channel.basic_consume(queue=self.callback_queue, on_message_callback=self.on_response, auto_ack=True)

            print("[", time.ctime(time.time()), "] -> Subscription ended.")
        