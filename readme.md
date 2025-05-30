# SD TASK 1

Authors:

- Gerard Roman
- Eric Riveiro

[Repository link](https://github.com/errivi/SD_TASK1)


## Description

The task implemented is about the implementation of four communication middleware for comparing its performance and scaling.

## Architecture

The middleware are XML-RPC, Pyro, Redis and RabbitMQ.We implemented a a server-client archictecture where we have an insult server,
filter insult server and some tests.

## System dependencies

To run all code with no problems you must check the middleware versions that you have on your PC. The dependencies used are:
    - XML-RPC: included in Python 
    - Pyro: Pyro 4.82
    - Redis: 5.2.1 on docker
    - RabbitMQ: 4.1.0 management on docker
    - Pika: 1.3.2
 
## Usage

To run the architecture implemented you must follow the next steps:
    - XML-RPC:
      1. By CLI execute Test.py with the number of nodes wanted.
    - Pyro:
      1. By CLI execute Test.py with the number of nodes wanted.
    - Redis:
      1. Get the redis container on Docker and set up default port 6379 or custom (you must change it in code).
      2. By CLI execute Test.py with the number of nodes wanted.
    - RabbitMQ:
      1. Get the rabbitmq container on Docker and set up default port 6379 or custom (you must change it in code).
      2. By CLI execute Test.py with the number of nodes wanted.

## Examples

The following examples are after setting up dependencies and located on SD_TASK1/middleware:

| Middleware | Example execution                                   |
|------------|-----------------------------------------------------|
| XML-RPC    | python SD_TASK1/xmlrpc/Test.py n                    |
| Pyro       | python SD_TASK1/pyro/Test.py n                      |
| Redis      | python SD_TASK1/redis/Test.py n                     |
| RabbitMQ   | python SD_TASK1/RabbitMQ/Test.py n                  |

Where n is an integer within 1 and 4 (5 and onwards the code becomes unstable, review the code before using it's numbers as significant data)
