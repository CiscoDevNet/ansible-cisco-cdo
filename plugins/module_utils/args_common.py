#!/usr/bin/python
# -*- coding: utf-8 -*-
#
# Apache License v2.0+ (see LICENSE or https://www.apache.org/licenses/LICENSE-2.0)

from __future__ import absolute_import, division, print_function

__metaclass__ = type

#############################
# Common to all modules
COMMON_SPEC = {
    "api_key": {"required": True, "type": "str", "no_log": True},
    "region": {"default": "us", "choices": ["us", "eu", "apj"], "type": "str"},
}

#############################
# Inventory
INVENTORY_ARGUMENT_SPEC = COMMON_SPEC | {
    "gather": {
        "type": "dict",
        "options": {
            "filter": {"type": "str"},
            "device_type": {"default": "all", "choices": ["all", "asa", "ios", "ftd", "fmc"]},
        },
    },
    "add": {
        "type": "dict",
        "options": {
            "ftd": {
                "type": "dict",
                "options": {
                    "name": {"default": "ftd", "type": "str"},
                    "is_virtual": {"default": False, "type": "bool"},
                    "onboard_method": {"default": "cli", "choices": ["cli", "ltp"], "type": "str"},
                    "access_control_policy": {"default": "Default Access Control Policy", "type": "str"},
                    "license": {
                        "type": "list",
                        "choices": ["BASE", "THREAT", "URLFilter", "MALWARE", "CARRIER", "PLUS", "APEX", "VPNOnly"],
                    },
                    "performance_tier": {
                        "choices": ["FTDv", "FTDv5", "FTDv10", "FTDv20", "FTDv30", "FTDv50", "FTDv100"],
                        "type": "str",
                    },
                    "retry": {"default": 10, "type": "int"},
                    "delay": {"default": 1, "type": "int"},
                    "serial": {"type": "str"},
                    "password": {"default": "", "type": "str"},
                },
            },
            "asa_ios": {
                "type": "dict",
                "options": {
                    "name": {"default": "", "type": "str"},
                    "ipv4": {"default": "", "type": "str"},
                    "port": {"default": 443, "type": "int"},
                    "sdc": {"default": "", "type": "str"},
                    "username": {"default": "", "type": "str"},
                    "password": {"default": "", "type": "str"},
                    "ignore_cert": {"default": False, "type": "bool"},
                    "device_type": {"default": "asa", "choices": ["asa", "ios"], "type": "str"},
                    "retry": {"default": 10, "type": "int"},
                    "delay": {"default": 1, "type": "int"},
                },
            },
        },
    },
    "delete": {
        "type": "dict",
        "options": {
            "name": {"required": True, "type": "str"},
            "device_type": {"required": True, "choices": ["asa", "ios", "ftd"], "type": "str"},
        },
    },
}

INVENTORY_REQUIRED_ONE_OF = ["gather", "add", "delete"]
INVENTORY_MUTUALLY_EXCLUSIVE = ["gather", "add", "delete"]
INVENTORY_REQUIRED_TOGETHER = []
INVENTORY_REQUIRED_IF = []

#############################
# Network Objects
NET_OBJS_ARGUMENT_SPEC = COMMON_SPEC | {
    "gather": {
        "type": "dict",
        "options": {
            "name": {"type": "str"},
            "network": {"type": "str"},
            "tags": {"type": "list"},
            "limit": {"default": 50, "type": "int"},
            "offset": {"default": 0, "type": "int"},
        },
    },
    "add": {
        "type": "dict",
        "options": {
            "name": {"required": True, "type": "str"},
            "network": {"required": True, "type": "str"},
            "description": {"required": True, "type": "str"},
        },
    },
    "update": {"type": "dict", "options": {"name": {"default": "ftd", "type": "str"}}},
    "delete": {
        "type": "dict",
        "options": {
            "name": {"required": True, "type": "str"},
            "device_type": {"required": True, "choices": ["asa", "ios", "ftd"], "type": "str"},
        },
    },
}
NET_OBJS_REQUIRED = ["gather", "add", "update", "delete"]
NET_OBJS_MUTUALLY_EXCLUSIVE = []
NET_OBJS_REQUIRED_TOGETHER = []
NET_OBJS_REQUIRED_IF = []
