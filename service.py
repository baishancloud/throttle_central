#!/usr/bin/env python2
# coding: utf-8

from throttle_central import front_service

services = {
    'front': {
        'module': front_service,
        'resource_dict': front_service.resource_dict,
    },
}
