#!/usr/bin/env python2
# coding: utf-8

import logging
import time

from pykit import threadutil
from throttle_central import service

logger = logging.getLogger(__name__)


def wait_to_start(slot_number):
    to_sleep = (slot_number + 0.5) - time.time()
    if to_sleep <= 0:
        to_sleep = 0.01

    time.sleep(to_sleep)


def wait_until_slot_end(slot_number):
    to_sleep = (slot_number + 1) - time.time()
    if to_sleep <= 0:
        to_sleep = 0.01

    time.sleep(to_sleep)


def start_assign(context, assign_threads, slot_number):
    for service_name, service_model in service.services.iteritems():
        if service_name in assign_threads:
            continue

        th = threadutil.start_daemon_thread(
            service_model['module'].assign, args=(context, slot_number,))

        assign_threads[service_name] = th


def check_assign_complete(assign_threads):
    for service_name in service.services.keys():
        th = assign_threads[service_name]
        if th.is_alive():
            logger.error('assign thread for: %s, not complete at: %f' % (
                service_name, time.time()))
        else:
            del(assign_threads[service_name])


def _run(context):
    assign_threads = {}

    while True:
        slot_number = int(round(time.time()))

        wait_to_start(slot_number)

        logger.info('start to assign at time: %f' % time.time())

        start_assign(context, assign_threads, slot_number)

        wait_until_slot_end(slot_number)

        check_assign_complete(assign_threads)


def run(context):
    while True:
        context['running'] = False

        try:
            logger.info('try to get lock at time: %f' % time.time())

            with context['Lock']():
                logger.info('got lock at time: %f' % time.time())
                context['running'] = True

                _run(context)

            context['running'] = False

        except Exception as e:
            context['running'] = False
            logger.exception('failed to run assigner: %s' % repr(e))
            time.sleep(3)
