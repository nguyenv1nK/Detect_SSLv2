# -*- coding: utf-8 -*-

__author__ = 'TOANTV'
import threading

import pika
from pika.exceptions import ConnectionClosed, ProbableAuthenticationError
from requests import RequestException
from retrying import retry

from .api import SecurityboxAPI
from .configuration import settings
from .logger import logger
from .runner import Runner


class Rabbitmq:
    def __init__(self, queue):
        # self.queue = "test"
        self.queue = "{0}_{1}".format(settings.config["global"]["node"], queue)
        self.dir_plugin = queue
        self.maxPriority = 255
        self.name = "Rabbitmq"
        self.web_api = SecurityboxAPI()
        self.connection = None

    def __del__(self):
        self.connection.close()

    @retry(wait_random_min=15000, wait_random_max=30000)
    def create_connection(self):
        try:
            credentials = pika.PlainCredentials(settings.config["broker"]["user"], settings.config["broker"]["pass"])
            self.connection = pika.BlockingConnection(
                pika.ConnectionParameters(
                    host=settings.config["broker"]["host"],
                    port=settings.config["broker"]["port"],
                    credentials=credentials,
                    blocked_connection_timeout=10)
            )

            self.channel = self.connection.channel()
            self.channel.queue_declare(queue=self.queue, durable=True)
        except ConnectionClosed, ex:
            logger.error(
                "Cannot connect to rabbitmq server {}:{}, retrying ....".format(settings.config["broker"]["host"],
                                                                                settings.config["broker"]["port"]))
            raise RequestException("Cannot connect to rabbitmq server, retrying ....")
        except ProbableAuthenticationError, ex:
            logger.error("Cannot authentication to rabbitmq server, please check the configs, retrying ....")
            raise RequestException("Cannot authentication to rabbitmq server, please check the configs, retrying ....")
        except Exception, ex:
            logger.error("Authentication to rabbitmq server is error, exceptions {}".format(str(ex)))
            raise RequestException("Authentication to rabbitmq server is error, retrying ....")

    def message_count(self):
        queue = self.channel.queue_declare(
            queue=self.queue, durable=True,
            exclusive=False, auto_delete=False
        )
        return queue.method.message_count

    def add(self, message):
        if self.connection is None:
            self.create_connection()
        self.channel.basic_publish(exchange='',
                                   routing_key=self.queue,
                                   body=message,
                                   properties=pika.BasicProperties(
                                       delivery_mode=2,  # make message longistent
                                   ))
        logger.info(data="Add message to queue is susscessfull!!!", plugin=self.name)
        self.connection.close()

    def get(self):
        if self.connection is None:
            self.create_connection()
        self.channel.basic_qos(prefetch_count=1)
        self.channel.basic_consume(self.callback, queue=self.queue)
        # self.channel.basic_consume(self.callback, queue=self.queue, no_ack=True)
        logger.info(data="Start rabbitmq consumer, waiitting for messages from queue {}".format(self.queue),
                    plugin=self.name)

        self.channel.start_consuming()

    def callback(self, ch, method, properties, body):
        try:
            logger.log(data=" [x] Received %r" % body, plugin=self.name)
            # run = Runner(web_api=self.web_api)
            thread = threading.Thread(target=connection_sleep, args=(self.connection, body,))
            thread.setDaemon(True)
            thread.start()
            Runner(self.web_api, self.dir_plugin).start(body)
            # scanner(self.web_api, self.dir_plugin, "", body)
            print(" [x] Finish recived %r" % body)
            logger.log(data=" [x] Finish received %r" % body, plugin=self.name)
            thread.stop = True
            thread.join()
            ch.basic_ack(delivery_tag=method.delivery_tag)
        except Exception as err:
            logger.log(data="callback rabbitmq error: {}".format(str(err)), plugin=self.name)
        logger.log(data="System exit !!", plugin=self.name)
        # ch.stop_consuming()

    def special_scan(self, script_name, link_id, is_link=True):
        if script_name == "":
            Runner(self.web_api, self.dir_plugin).start(link_id, is_link=is_link)
        else:
            Runner(self.web_api, self.dir_plugin).special_scan(script_name, link_id, is_link)

    def special_task(self, task):
        list_link = self.web_api.get_list_link(task=task)
        for link in list_link:
            Runner(self.web_api, self.dir_plugin).start(link["id"])


def connection_sleep(connection, body):
    print("+++ Connection process data events, scan id: " + str(body))
    t = threading.currentThread()
    while not getattr(t, "stop", False):
        connection.sleep(10)

# def scanner(web_api, queue_name, script_scan, link_id):
#     if script_scan == "":
#         Runner(web_api, queue_name).start(link_id)
#     else:
#         Runner(web_api, queue_name).special_scan(script_scan, link_id)
