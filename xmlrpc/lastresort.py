import asyncio
import aiohttp
import time
import sys

TOTAL_REQUESTS = 1_000
NUM_SERVERS = int(sys.argv[1]) if len(sys.argv) > 1 and int(sys.argv[1]) > 0 and int(sys.argv[1]) < 5 else 1

async def send_post(session, url, data, request_id, responses):
    try:
        async with session.post(url, data=data, headers={'Content-Type': 'application/xml'}) as response:
            # Read response text (if needed)
            response_text = await response.text()
            # Store success status
            responses[request_id] = True
    except Exception as e:
        responses[request_id] = False
        print(f"Request {request_id} failed: {e}")

async def main():
    url = ['http://127.0.0.1:8000/RPC2', 'http://127.0.0.1:8001/RPC2', 'http://127.0.0.1:8002/RPC2', 'http://127.0.0.1:8003/RPC2']  # replace with your target port
    xml_data = '''<?xml version='1.0'?>
<methodCall>
    <methodName>insult</methodName>
    <params></params>
</methodCall>'''

    number_of_requests = TOTAL_REQUESTS  # or any number you want to send
    responses = {}  # to track responses
    RR_uri = 0
    num_uri = NUM_SERVERS

    async with aiohttp.ClientSession() as session:
        tasks = []
        delta = time.perf_counter()
        for i in range(number_of_requests):
            # Launch requests asynchronously without waiting
            task = asyncio.create_task(send_post(session, url[RR_uri], xml_data, i, responses))
            tasks.append(task)
            RR_uri += 1
            if(RR_uri >= num_uri): RR_uri = 0

        # Optional: wait for all requests to complete
        await asyncio.gather(*tasks)
        return (time.perf_counter() - delta)

    # After all requests are done, check responses
    all_success = all(responses.get(i, False) for i in range(number_of_requests))
    print(f"\nAll requests succeeded: {all_success}")
    for i in range(number_of_requests):
        print(f"Request {i} success: {responses.get(i, False)}")

if __name__ == '__main__':
    took = asyncio.run(main())
    print(f"Took {took} to make {TOTAL_REQUESTS} reqs for {NUM_SERVERS} servers, got {TOTAL_REQUESTS/took} reqs/s")