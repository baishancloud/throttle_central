#!/usr/bin/env python2
# coding: utf-8

import logging
import time

from pykit import ratelimiter
from throttle_central import central_util

logger = logging.getLogger(__name__)

resource_dict = {
    'traffic_up': 0,
    'traffic_down': 0,
    'database_read': 0,
    'database_write': 0
}


class FrontService(object):
    def __init__(self):
        self.curr_slot = int(time.time())
        self.quota = {}
        self.limiters = {}
        # second
        self.slot_window_size = 5
        self.service = 'front'

    def consume(self, slot_number, consumptions):
        logger.debug("receive:%s" % repr(consumptions))
        for user, user_consumption in consumptions.items():
            if user not in self.limiters:
                continue
            for resource in resource_dict.keys():
                resource_limiter = self.limiters[user][resource]
                resource_limiter.consume(user_consumption.get(resource, 0))

    def get_quota(self, slot_number, nid):
        slot_number = slot_number + 1

        if slot_number not in self.quota:
            logger.info("slot:%s not found", slot_number)
            return {slot_number: {}}
        if nid not in self.quota[slot_number]:
            logger.info("node_id:%s in slot:%s not found", nid, slot_number)
            return {slot_number: {}}

        return {slot_number: self.quota[slot_number][nid]}

    def assign(self, context, slot_number):
        self.curr_slot = slot_number

        self._update_limiters(context)

        self._assign(context, self.curr_slot + 2)

        logger.debug("assign:%s" % repr(self.quota))
        logger.debug("dist:%s" % repr(context['distribution']))

    def _update_limiters(self, context):

        limits = context['list_limits'](self.service)

        users = [x['username'] for x in limits]

        logger.debug('limits:%s' % repr(limits))
        for user_limit in limits:
            user = user_limit['username']
            limit = user_limit['limit']

            if user not in self.limiters:
                self.limiters[user] = {}
                for resource in resource_dict.keys():
                    token_per_second = limit[resource]
                    self.limiters[user][resource] = ratelimiter.RateLimiter(
                        token_per_second, 10 * token_per_second)
                continue

            for resource in resource_dict.keys():
                token_per_second = limit[resource]
                resource_limiter = self.limiters[user][resource]
                resource_limiter.set_token_per_second(token_per_second)
                resource_limiter.set_capacity(10 * token_per_second)

        for user, _ in self.limiters.items():
            if user not in users:
                del self.limiters[user]

    def _assign(self, context, slot_number):

        self.quota[slot_number] = {}

        for user, resource_limiters in self.limiters.iteritems():
            for resource in resource_dict.keys():

                total_stored = resource_limiters[resource].get_stored()

                if total_stored < 0:
                    total_stored = 0

                report_slot_number = self.curr_slot - 1

                nodes, total_consumption, total_rejection = self._get_last_report(
                    context, report_slot_number, user, resource)
                if len(nodes) == 0:
                    logger.info('u:%s,r:%s:nodes size 0' % (user, resource))
                    continue

                reserved_for_zero, zero_request_nodes = self._reserve_for_zero(
                    nodes)

                for nid, resource_st in nodes.items():
                    consumption = resource_st['consumption']
                    rejection = resource_st['rejection']

                    if consumption == 0 and rejection == 0:
                        expected_weight = reserved_for_zero / \
                            len(zero_request_nodes)
                    else:
                        expected_weight = self._get_expected_weight(
                            consumption, rejection, total_consumption, total_rejection) * (
                            1 - reserved_for_zero)

                    next_assign = total_stored * expected_weight

                    if nid not in self.quota[slot_number]:
                        self.quota[slot_number][nid] = {}
                    if user not in self.quota[slot_number][nid]:
                        self.quota[slot_number][nid][user] = {}
                    self.quota[slot_number][nid][user][resource] = next_assign

        central_util.remove_outdated_slot(self.quota, slot_number,
                                          context['nr_slot'])

    @staticmethod
    def _reserve_for_zero(nodes):
        zero_request_nodes = []
        for nid, resource_st in nodes.items():
            if resource_st['consumption'] == 0 and resource_st['rejection'] == 0:
                zero_request_nodes.append(nid)
        if len(zero_request_nodes) == len(nodes):
            reserved_for_zero = 1.0
        else:
            reserved_for_zero = float(
                len(zero_request_nodes)) / len(nodes) * 0.1
        return reserved_for_zero, zero_request_nodes

    def _get_last_report(self, context, n_slot_number, user, resource):

        nodes = context['distribution'].get(
            self.service, {}).get(user, {}).get(resource, {})
        return_nodes = {}

        total_consumption = 0
        total_rejection = 0

        for nid, resource_st in nodes.items():
            if n_slot_number - self.slot_window_size < resource_st['slot_number'] <= n_slot_number:
                weight = self.slot_window_size - \
                    (n_slot_number - resource_st['slot_number'])

                return_nodes[nid] = {
                    'consumption': resource_st.get('consumption', 0) * weight,
                    'rejection': resource_st.get('rejection', 0) * weight
                }

                total_consumption += return_nodes[nid]['consumption']
                total_rejection += return_nodes[nid]['rejection']

        return return_nodes, total_consumption, total_rejection

    @staticmethod
    def _get_expected_weight(consumption, rejection, total_consumption, total_rejection):
        if total_consumption > 0 and total_rejection > 0:
            expected_weight = float(consumption) / total_consumption * 0.6 + float(
                rejection) / total_rejection * 0.4
        elif total_consumption == 0 and total_rejection == 0:
            expected_weight = 0
        elif total_consumption == 0:
            expected_weight = float(rejection) / total_rejection
        else:
            expected_weight = float(consumption) / total_consumption

        return expected_weight


front_service = FrontService()


def consume(context, slot_number, service_consumption):
    front_service.consume(slot_number, service_consumption)


def get_quota(context, slot_number, node_id):
    return front_service.get_quota(slot_number, node_id)


def assign(context, slot_number):
    try:
        front_service.assign(context, slot_number)
    except Exception as e:
        logger.exception('failed to assign %s:' % slot_number + repr(e))
