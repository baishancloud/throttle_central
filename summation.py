#!/usr/bin/env python2
# coding: utf-8

import copy

from pykit import dictutil
from throttle_central import central_util
from throttle_central import service


def get_zero_dict(service_name):
    return copy.deepcopy(service.services[service_name]['resource_dict'])


def get_empty_user_distribution(service_name):
    empty_user_distribution = {}
    resource_names = service.services[service_name]['resource_dict'].keys()

    for resource_name in resource_names:
        empty_user_distribution[resource_name] = {}

    return empty_user_distribution


def update_distribution(distribution, service_name, user_name, node_id,
                        slot_number, user_consumption, user_rejection):
    service_distribution = distribution[service_name]

    if user_name not in service_distribution:
        service_distribution[user_name] = get_empty_user_distribution(
            service_name)

    user_distribution = service_distribution[user_name]

    for resource_name, resource_distribution in user_distribution.iteritems():
        resource_distribution[node_id] = {
            'slot_number': slot_number,
            'consumption': user_consumption.get(resource_name, 0),
            'rejection': user_rejection.get(resource_name, 0),
        }


def service_distribution_update(distribution, slot_number, service_name,
                                node_id, service_consumption,
                                service_rejection):
    if service_name not in distribution:
        distribution[service_name] = {}

    user_names = list(set(service_consumption.keys()
                          ).union(service_rejection.keys()))

    for user_name in user_names:
        user_consumption = service_consumption.get(
            user_name) or get_zero_dict(service_name)

        user_rejection = service_rejection.get(
            user_name) or get_zero_dict(service_name)

        update_distribution(distribution, service_name, user_name, node_id,
                            slot_number, user_consumption, user_rejection)


def do_sum(context, node_id, message):
    # message sent in this slot contain data of last slot
    slot_number = message['slot_number'] - 1

    consumption_sum = context['consumption_sum']
    rejection_sum = context['rejection_sum']
    distribution = context['distribution']

    consumption = message['consumption']
    rejection = message['rejection']

    if slot_number not in consumption_sum:
        consumption_sum[slot_number] = {}
        central_util.remove_outdated_slot(
            consumption_sum, slot_number, context['nr_slot'])

        rejection_sum[slot_number] = {}
        central_util.remove_outdated_slot(
            rejection_sum, slot_number, context['nr_slot'])

    dictutil.addto(consumption_sum[slot_number], consumption)

    dictutil.addto(rejection_sum[slot_number], rejection)

    for service_name in consumption.keys():
        service_consumption = consumption[service_name]
        service_rejection = rejection[service_name]

        service_distribution_update(distribution, slot_number, service_name,
                                    node_id, service_consumption,
                                    service_rejection)
