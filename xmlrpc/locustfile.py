import time
import random
from xmlrpc.client import ServerProxy, Fault
from locust import User, task

class XmlRpcClient(ServerProxy):
    """
    XmlRpcClient is a tailored version of the standard library's ServerProxy.
    It captures function calls and triggers the *request* event upon completion, ensuring the calls are logged.
    """

    def __init__(self, host, request_event):
        super().__init__(random.choice(str.split(host, ',')))
        self._request_event = request_event

    def __getattr__(self, name):
        func = ServerProxy.__getattr__(self, name)

        def wrapper(*args, **kwargs):
            start_time = time.perf_counter()
            request_meta = {
                "request_type": "xmlrpc",
                "name": name,
                "response_length": 0,
                "response": None,
                "context": {},  # Refer to HttpUser for context implementation details
                "exception": None,
            }
            try:
                request_meta["response"] = func(*args, **kwargs)
            except Fault as e:
                request_meta["exception"] = e
            request_meta["response_time"] = (time.perf_counter() - start_time) * 1000
            self._request_event.fire(**request_meta)  # Logging the request
            return request_meta["response"]

        return wrapper

class XmlRpcUser(User):
    abstract = True  # Ensures that this isn't instantiated as an actual user

    def __init__(self, environment):
        super().__init__(environment)
        self.client = XmlRpcClient(self.host, request_event=environment.events.request)

# The user class that is instantiated for testing
class MyUser(XmlRpcUser):
    @task
    def insultMe(self):
        self.client.insult()