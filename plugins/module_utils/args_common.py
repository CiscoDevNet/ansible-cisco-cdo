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
# Inventory module
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
                    "retry": {"type": "int", "required": False, "default": 10},
                    "delay": {"type": "int", "required": False, "default": 1},
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
                    "serial": {"type": "str"},
                    "password": {"type": "str"},
                },
            },
            "asa_ios": {
                "type": "dict",
                "options": {
                    "device_name": {"required": True, "type": "str"},
                    "ipv4": {"required": True, "type": "str"},
                    "mgmt_port": {"default": 443, "type": "int"},
                    "sdc": {"required": True, "type": "str"},
                    "username": {"required": True, "type": "str"},
                    "password": {"required": True, "type": "str"},
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
# Deploy Changes module
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
            "device_name": {"required": True, "type": "str"},
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
# Commands module
CMD_ARGUMENT_SPEC = COMMON_SPEC | {
    "exec_command": {
        "type": "dict",
        "options": {
            "device_type": {"default": "asa", "choices": ["all", "asa", "ios"]},
            "device_name": {"required": True, "type": "str"},
            "cmd_list": {"required": True, "type": "list"},
            "retries": {"default": 20, "type": "int"},
            "interval": {"default": 2, "type": "int"},
        },
    },
    "apply_template": {
        "type": "dict",
        "options": {
            "device_type": {"default": "asa", "choices": ["all", "asa", "ios"]},
            "device_name": {"required": True, "type": "str"},
            "retries": {"default": 20, "type": "int"},
            "interval": {"default": 2, "type": "int"},
            "config": {"required": True, "type": "dict"},
        },
    },
}
CMD_MUTUALLY_REQUIRED_ONE_OF = ["exec_command", "load_config", "clear_config", "apply_template"]
CMD_MUTUALLY_EXCLUSIVE = []
CMD_REQUIRED_TOGETHER = []
CMD_REQUIRED_IF = []

#############################
# Config module
CONFIG_ARGUMENT_SPEC = COMMON_SPEC | {
    "config": {
        "type": "dict",
        "options": {
            "device_uid": {"type": "str"},
        },
    },
}
CONFIG_MUTUALLY_REQUIRED_ONE_OF = ["config"]
CONFIG_MUTUALLY_EXCLUSIVE = []
CONFIG_REQUIRED_TOGETHER = []
CONFIG_REQUIRED_IF = []

#############################
# Tenant module
#############################
# Config module
TENANT_ARGUMENT_SPEC = COMMON_SPEC | {
    "info": {
        "type": "dict",
        "options": {
            "features": {"default": True, "type": "bool"},
        },
    },
    "users": {
        "type": "dict",
        "options": {
            "get": {"default": True, "type": "bool"},
        },
    },
}
TENANT_MUTUALLY_REQUIRED_ONE_OF = ["info", "users"]
TENANT_MUTUALLY_EXCLUSIVE = []
TENANT_REQUIRED_TOGETHER = []
TENANT_REQUIRED_IF = []

###############################
# Access Control Policy module
###############################
ACP_ARGUMENT_SPEC = COMMON_SPEC | {
    "gather": {
        "type": "dict",
        "options": {
            "name": {"required": True, "type": "str"},
            "acp_name": {"type": "str"},
        },
    },
}
ACP_MUTUALLY_REQUIRED_ONE_OF = ["gather"]
ACP_MUTUALLY_EXCLUSIVE = []
ACP_REQUIRED_TOGETHER = []
ACP_REQUIRED_IF = []
