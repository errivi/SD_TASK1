import pika
import threading as th
import uuid
import time

class ThreadWithReturnValue(th.Thread):
    def __init__(self, group=None, target=None, name=None,
                 args=(), kwargs={}, Verbose=None):
        th.Thread.__init__(self, group, target, name, args, kwargs)
        self._return = None

    def run(self):
        if self._target is not None:
            self._return = self._target(*self._args,
                                                **self._kwargs)
    def join(self, *args):
        th.Thread.join(self, *args)
        return self._return

def _on_response(self, ch, method, props, body):
    return body

class RabbitMQ_ClientAPI:
    """Class that acts as a simplification API for clients to easily send messages and recieve responses to/from RabbitMQ"""
    def __init__(self, host='127.0.0.1', port=5672, method_queue=None, username='guest', password='guest', virtual_host='/', heartbeat=60):
        self.connection_params = pika.ConnectionParameters(
            host=host,
            port=port,
            virtual_host=virtual_host,
            credentials=pika.PlainCredentials(username, password),
            heartbeat=heartbeat
        )
        self._methods_queue = method_queue
        self.connection = None
        self.channel = None
        self.consumer_thread = None
        self._consume_queue = str(uuid.uuid4())
        self._response = None
        self._stop_flag = th.Event()

    def connect(self):
        """Establish connection and channel."""
        self.connection = pika.BlockingConnection(self.connection_params)
        self.channel = self.connection.channel()
        self.channel.queue_declare(queue=self._consume_queue, durable=False, auto_delete=True)
        print("Is connection opened? ", self.connection.is_open)
    
    def close(self):
        """Close the connection and basically factory reset the instance"""
        try: self.stop_consuming()
        except: pass
        if self.channel is not None:
            self.channel.close()
            self.channel = None
        if self.connection is not None:
            self.connection.close()
            self.connection = None
        self._consume_queue = None
        self._methods_queue = None
        self._stop_flag.clear()

    def declare_queue(self, queue_name, durable=True):
        """Declare a queue."""
        if not self.channel:
            self.connect()
        self.channel.queue_declare(queue=queue_name, durable=durable)

    def publish_method(self, queue_name, method:str, args:str="", routing_key=None, persistent=True):
        """Send a message to a queue."""
        if not self.channel:
            self.connect()
        if not self._consume_queue:
            self._consume_queue = str(uuid.uuid4())
        properties = pika.BasicProperties(type=method, delivery_mode=2 if persistent else 1, reply_to=self._consume_queue)
        self.channel.basic_publish(
            exchange='',
            routing_key=routing_key or queue_name,
            body=args,
            properties=properties
        )

    def start_consuming(self, queue_name, callback, auto_ack=True):
        """
        Start consuming messages from a queue.
         - callback should be a function accepting 4 parameters: (channel, method, properties, body)
        """
        if not self.channel:
            self.connect()
        self._consume_queue = queue_name

        def _consume(stop:th.Event):
            while not stop.is_set():
                method_frame, properties, body = self.channel.consume(queue=queue_name, auto_ack=auto_ack)
                if method_frame:
                    result = callback(self.channel, method_frame, properties, body)
                    if auto_ack:
                        self.channel.basic_ack(delivery_tag=method_frame.delivery_tag)
                    if result is not None: stop.set()

        # Run consuming in a separate thread
        self.consumer_thread = ThreadWithReturnValue(target=_consume, args=(self._stop_flag,))
        self.consumer_thread.start()

    def acknowledge_message(self, delivery_tag):
        """Acknowledge a message."""
        if self.channel:
            self.channel.basic_ack(delivery_tag=delivery_tag)

    def stop_consuming(self):
        """Stop consuming messages."""
        if self.consumer_thread:
            self._stop_flag.set()
            self.consumer_thread.join(timeout=2)
            self.consumer_thread = None
        if self.channel:
            self.channel.stop_consuming()

    def setMethodQueue(self, method_queue:str):
        self._methods_queue = method_queue

    def call(self, method:str, args:str=""):
        if not self._methods_queue: raise Exception("Attempted to call a method without constructing a connection first (up until queue selected state required).")
        if not self.channel: self.connect()
        
        global _results
        self.start_consuming(queue_name=self._consume_queue, callback=_on_response, auto_ack=True)
        time.sleep(7)
        self.publish_method(queue_name=self._methods_queue, method=method, args=args)
        self.publish_method(queue_name=self._methods_queue, method=method)
        #iter = 0
        #while _results is None:
            #time.sleep(0.00001)#self.connection.sleep(0.00001)
            #iter += 1
            #if iter > 10_000: print("Waited too long :("); break
            #print("_results is: ", _results)
            #self.connection.process_data_events()
        try: return self.consumer_thread.join().decode()
        except: return "NoResponse"
        finally:
            _results = None
            self.stop_consuming()

    def multicall(self, method:str, reps:int=100):
        if not self._methods_queue: raise Exception("Attempted to call a method without constructing a connection first (up until queue selected state required).")
        if not self.channel: self.connect()
        
        global _results
        self.start_consuming(queue_name=self._consume_queue, callback=_on_response, auto_ack=True)
        for _ in range(reps):
            self.publish_method(queue_name=self._methods_queue, method=method)
            self.consumer_thread.join()
            #while _results is None:
            #    time.sleep(0.00001)#self.connection.sleep(0.00001)
            #    #print("_results is ", _results)
            #    #try: self.connection.process_data_events()
            #    #except: pass
            #_results = None
        self.stop_consuming()
    
    def subscribeTo(self, exchange_name:str, queue_name:str):
        if not self.channel: self.connect()
        
        self.channel.exchange_declare(exchange=exchange_name, exchange_type='fanout')
        self.channel.queue_declare(queue=self._consume_queue, exclusive=True)
        self.channel.queue_bind(exchange=exchange_name, queue=queue_name)

        print(f"[Receiver] Waiting for insults... (Queue: {queue_name})")

        def subscription_work(ch, method, properties, body):
            print("[", time.ctime(time.time()), "] -> Got insult: ", body.decode())

        self.channel.basic_consume(queue=queue_name, on_message_callback=subscription_work, auto_ack=True)