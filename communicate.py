#!/usr/bin/env python2
# coding: utf-8

import logging
import threading
import time
import uuid
from collections import OrderedDict

from geventwebsocket import Resource
from geventwebsocket import WebSocketApplication
from geventwebsocket import WebSocketServer

from pykit import utfjson
from throttle_central import central_util
from throttle_central import monitor_api
from throttle_central import service

logger = logging.getLogger(__name__)

global_value = {}


LOCK = threading.RLock()


def update_reported(slot_number, node_id, port, message):
    with LOCK:
        reported = global_value['context']['reported']
        if reported.get(slot_number) == None:
            reported[slot_number] = {}
            nr_slot = global_value['context']['nr_slot']
            central_util.remove_outdated_slot(reported, slot_number, nr_slot)

        if reported[slot_number].get(node_id) == None:
            reported[slot_number][node_id] = {}

        reported[slot_number][node_id][port] = message


def enqueue_message(message_info):
    message_queue = global_value['context']['message_queue']
    message_queue.put(message_info)


def get_quota(message):
    consumption = message['consumption']
    slot_number = message['slot_number']
    node_id = message['node_id']

    node_quota = {}

    for service_name in consumption.keys():
        service_model = service.services[service_name]

        node_quota[service_name] = service_model['module'].get_quota(
            global_value['context'], slot_number, node_id)

    context = global_value['context']
    if slot_number not in context['quota']:
        context['quota'][slot_number] = {}

    context['quota'][slot_number][node_id] = node_quota
    nr_slot = global_value['context']['nr_slot']
    central_util.remove_outdated_slot(context['quota'], slot_number, nr_slot)

    return node_quota


class ThrottleWebSocketApplication(WebSocketApplication):

    def on_open(self):
        self.conn_uuid = uuid.uuid4().hex[1:10]

        if not global_value['context']['running']:
            logger.info('assigner is not running, refuse connection')
            self.ws.close()
            return

        client_address = self.protocol.handler.client_address
        client_ip = client_address[0]
        client_port = client_address[1]

        self.conn_info = {
            'client_ip': client_ip,
            'client_port': client_port,
            'conn_uuid': self.conn_uuid,
            'connect_time': time.time(),
        }

        global_value['context']['connections'][self.conn_uuid] = self.conn_info

        logger.info('%s=> new connection: %s %d, now total: %d' % (
            self.conn_uuid, client_ip, client_port,
            len(global_value['context']['connections'])))

    def on_message(self, message_str):
        if message_str == None:
            return

        if not global_value['context']['running']:
            logger.info('%s=> assigner is not running, close connection' %
                        self.conn_info['conn_uuid'])
            self.ws.close()
            return

        self.process_message(message_str)

    def on_close(self, reason):
        if self.conn_uuid in global_value['context']['connections']:
            del(global_value['context']['connections'][self.conn_uuid])

        logger.info('%s=> close connection for: %s, now total: %d' % (
            self.conn_uuid, str(reason),
            len(global_value['context']['connections'])))

    def process_message(self, message_str):
        message = utfjson.load(message_str)
        if 'monitor' in message:
            self.process_monitor(message)
        else:
            self.process_report(message)

    def process_monitor(self, message):
        resp = monitor_api.get_monitor_resp(message)
        self.send_json(resp)

    def process_report(self, message):
        slot_number = message['slot_number']
        node_id = message['node_id']

        message['receive_time'] = time.time()
        update_reported(slot_number, node_id,
                        self.conn_info['client_port'], message)

        message_info = {
            'conn_info': self.conn_info,
            'message': message,
        }

        logger.info('%s=> at time: %f, start to process report' % (
            self.conn_info['conn_uuid'], time.time()))

        try:
            enqueue_message(message_info)
            quota = get_quota(message_info['message'])
        except Exception as e:
            logger.exception('got exception when process report: ' + repr(e))
            self.ws.close()
            return

        logger.info('%s=> at time: %f, return quota, slot: %d' % (
            self.conn_info['conn_uuid'], time.time(), slot_number))

        self.send_json(quota)

    def send_json(self, value):
        value_str = utfjson.dump(value)
        self.ws.send(value_str)


def run(context):
    global_value['context'] = context
    WebSocketServer(
        (context['ip'], context['port']),
        Resource(OrderedDict({'/': ThrottleWebSocketApplication})),
    ).serve_forever()
