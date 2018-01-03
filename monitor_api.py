#!/usr/bin/env python2
# coding: utf-8


def get_connections(message, container):
    return container


def get_slots(message, container):
    start_slot = message.get('start_slot')
    if start_slot == None:
        return container

    end_slot = message.get('end_slot', start_slot)

    result = {}

    for slot_number in range(start_slot, end_slot + 1):
        if slot_number in container:
            result[slot_number] = container[slot_number]

    return result


HANDLER = {
    'connections': get_connections,
    'reported': get_slots,
    'consumption_sum': get_slots,
    'rejection_sum': get_slots,
    'distribution': get_slots,
    'quota': get_slots,
}


def get_monitor_resp(context, message):
    subject = message['monitor']
    container = context.get(subject)
    handler = HANDLER.get(subject)

    if container is None or handler is None:
        return {'error_code': 'InvalidSubject',
                'error_message': 'invalid subject: %s' % subject}

    return handler(message, container)
