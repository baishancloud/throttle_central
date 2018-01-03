#!/usr/bin/env python2
# coding: utf-8

import logging

from throttle_central import service
from throttle_central import summation

logger = logging.getLogger(__name__)


def process_consumption(context, slot_number, consumption):
    for service_name, service_consumption in consumption.iteritems():
        service_model = service.services[service_name]

        service_model['module'].consume(context, slot_number,
                                        service_consumption)


def process_message(context, message_info):
    logger.info('%s=> start to process message from: %s:%d' % (
                message_info['conn_info']['conn_uuid'],
                message_info['conn_info']['client_ip'],
                message_info['conn_info']['client_port']))

    message = message_info['message']

    # message sent in this slot contain data of last slot
    process_consumption(context, message['slot_number'] - 1,
                        message['consumption'])

    node_id = message['node_id']

    summation.do_sum(context, node_id, message)


def run(context):
    while True:
        message_info = context['message_queue'].get()
        try:
            process_message(context, message_info)
        except Exception as e:
            logger.exception('failed to process message: ' + repr(e))
