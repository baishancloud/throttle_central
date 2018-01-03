#!/usr/bin/env python2
# coding: utf-8

import logging
import Queue

from pykit import threadutil
from throttle_central import assigner
from throttle_central import communicate
from throttle_central import message_processor

logger = logging.getLogger(__name__)


def run(**argkv):
    context = {
        # websocket listen ip and port
        'ip': argkv.get('ip', '127.0.0.1'),
        'port': argkv.get('port', 32345),

        # every message received will be put into messgee queue,
        # and processed by message processor
        'message_queue': Queue.Queue(1024 * 10),

        # info in destribution will be used by function assign()
        'distribution': {},

        # for monitoring
        'connections': {},
        'reported': {},
        'consumption_sum': {},
        'rejection_sum': {},
        'quota': {},

        # specify how many slot to save in a dict contain info by slot
        # normally, only recent slots should be kept
        'nr_slot': argkv.get('nr_slot', 60),

        # a global lock class which can be used in 'with' statement.
        # it is used to make sure only one central node acutally working
        # at any time.
        'Lock': argkv['Lock'],

        # who got lock, who running
        'running': False,

        # callback function to get all limits setted for a service
        'list_limits': argkv['list_limits'],
    }

    threadutil.start_daemon_thread(assigner.run, args=(context,))

    threadutil.start_daemon_thread(message_processor.run, args=(context,))

    communicate.run(context)
