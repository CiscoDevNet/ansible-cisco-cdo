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
                    "device_name": {"required": True, "type": "str"},
                    "onboard_method": {"default": "cli", "choices": ["cli", "ltp"], "type": "str"},
                    "access_control_policy": {"default": "Default Access Control Policy", "type": "str"},
                    "is_virtual": {"default": False, "type": "bool"},
                    "license": {
                        "type": "list",
                        "choices": ["BASE", "THREAT", "URLFilter", "MALWARE", "CARRIER", "PLUS", "APEX", "VPNOnly"],
                        "default": ["BASE"],
                    },
                    "performance_tier": {
                        "choices": ["FTDv", "FTDv5", "FTDv10", "FTDv20", "FTDv30", "FTDv50", "FTDv100"],
                        "type": "str",
                    },
                    "retry": {"default": 10, "type": "int"},
                    "delay": {"default": 1, "type": "int"},
                    "serial": {"type": "str"},
                    "password": {"type": "str"},
                },
            },
            "asa_ios": {
                "type": "dict",
                "options": {
                    "device_name": {"required": True, "type": "str"},
                    "ipv4": {"type": "str"},
                    "mgmt_port": {"default": 443, "type": "int"},
                    "sdc": {"type": "str"},
                    "username": {"type": "str"},
                    "password": {"type": "str"},
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
            "device_name": {"required": True, "type": "str"},
            "device_type": {"required": True, "choices": ["asa", "ios", "ftd"], "type": "str"},
        },
    },
}

INVENTORY_REQUIRED_ONE_OF = ["gather", "add", "delete"]
INVENTORY_MUTUALLY_EXCLUSIVE = []
INVENTORY_REQUIRED_TOGETHER = []
INVENTORY_REQUIRED_IF = []

#############################
# Network Objects
NET_OBJS_ARGUMENT_SPEC = COMMON_SPEC | {
    "gather": {
        "type": "dict",
        "options": {
            "device_name": {"type": "str"},
            "network": {"type": "str"},
            "tags": {"type": "list"},
            "limit": {"default": 50, "type": "int"},
            "offset": {"default": 0, "type": "int"},
        },
    },
    "add": {
        "type": "dict",
        "options": {
            "device_name": {"required": True, "type": "str"},
            "network": {"required": True, "type": "str"},
            # Descriptions will be reworked in future CDO work fall of 2023 so omitting for meow
            # "description": {"required": True, "type": "str"},
        },
    },
    "update": {"type": "dict", "options": {"device_name": {"default": "ftd", "type": "str"}}},
    "delete": {
        "type": "dict",
        "options": {
            "device_name": {"required": True, "type": "str"},
            "device_type": {"required": True, "choices": ["asa", "ios", "ftd"], "type": "str"},
        },
    },
}
NET_OBJS_REQUIRED = ["gather", "add", "update", "delete"]
NET_OBJS_MUTUALLY_EXCLUSIVE = []
NET_OBJS_REQUIRED_TOGETHER = []
NET_OBJS_REQUIRED_IF = []

#############################
# Deploy Changes
DEPLOY_ARGUMENT_SPEC = COMMON_SPEC | {
    "deploy": {
        "type": "dict",
        "options": {
            "device_type": {"default": "all", "choices": ["all", "asa"]},
            "device_name": {"required": True, "type": "str"},
            "timeout": {"default": 20, "type": "int"},
            "interval": {"default": 2, "type": "int"},
        },
    },
    "pending": {
        "type": "dict",
        "options": {
            "device_type": {"default": "all", "choices": ["all", "asa"], "type": "str"},
            "device_name": {"type": "str"},
            "limit": {"default": 50, "type": "int"},
            "offset": {"default": 0, "type": "int"},
        },
    },
}
DEPLOY_MUTUALLY_REQUIRED_ONE_OF = ["deploy", "pending"]
DEPLOY_MUTUALLY_EXCLUSIVE = []
DEPLOY_REQUIRED_TOGETHER = []
DEPLOY_REQUIRED_IF = []

#############################
# Commands
CMD_ARGUMENT_SPEC = COMMON_SPEC | {
    "exec_command": {
        "type": "dict",
        "options": {
            "device_type": {"default": "all", "choices": ["all", "asa", "ios"]},
            "device_name": {"required": True, "type": "str"},
            "cmd_list": {"required": True, "type": "list"},
            "timeout": {"default": 20, "type": "int"},
            "interval": {"default": 2, "type": "int"},
        },
    },
}
CMD_MUTUALLY_REQUIRED_ONE_OF = ["exec_command"]
CMD_MUTUALLY_EXCLUSIVE = []
CMD_REQUIRED_TOGETHER = []
CMD_REQUIRED_IF = []
