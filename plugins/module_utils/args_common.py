#############################
# Common to all modules
COMMON_SPEC = {
    "api_key": {"required": True, "type": "str", "no_log": True},
    "region": {"default": "us", "choices": ["us", "eu", "apj"], "type": "str"},
}

#############################
# Add ASA and IOS
ADD_ASA_IOS_SPEC = COMMON_SPEC | {
    "add_asa_ios": {
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
}
ADD_ASA_IOS_REQUIRED_ONE_OF = ["add_asa_ios"]
ADD_ASA_IOS_MUTUALLY_EXCLUSIVE = []
ADD_ASA_IOS_REQUIRED_TOGETHER = []
ADD_ASA_IOS_REQUIRED_IF = []

#############################
# Add FTD
ADD_FTD_SPEC = COMMON_SPEC | {
    "add_ftd": {
        "type": "dict",
        "options": {
            "name": {"required": True, "type": "str"},
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
}
ADD_FTD_REQUIRED_ONE_OF = ["add_ftd"]
ADD_FTD_MUTUALLY_EXCLUSIVE = []
ADD_FTD_REQUIRED_TOGETHER = []
ADD_FTD_REQUIRED_IF = []

#############################
# Delete
DELETE_SPEC = COMMON_SPEC | {
    "delete": {
        "type": "dict",
        "options": {
            "filter": {"type": "str"},
            "name": {"required": True, "type": "str"},
            "device_type": {"required": True, "choices": ["asa", "ios", "ftd"], "type": "str"},
        },
    },
}
DELETE_REQUIRED_ONE_OF = ["delete"]
DELETE_MUTUALLY_EXCLUSIVE = []
DELETE_REQUIRED_TOGETHER = []
DELETE_REQUIRED_IF = []

#############################
# Inventory
INVENTORY_ARGUMENT_SPEC = COMMON_SPEC | {
    "inventory": {
        "type": "dict",
        "options": {
            "filter": {"type": "str"},
            "device_type": {"default": "all", "choices": ["all", "asa", "ios", "ftd", "fmc"]},
        },
    },
}

INVENTORY_REQUIRED_ONE_OF = ["inventory"]
INVENTORY_MUTUALLY_EXCLUSIVE = []
INVENTORY_REQUIRED_TOGETHER = []
INVENTORY_REQUIRED_IF = []


#############################
# Network Objects
NET_OBJS_ARGUMENT_SPEC = COMMON_SPEC | {
    "net_objects": {
        "type": "dict",
        "options": {
            "filter": {"type": "str"},
            "tags": {"type": "str"},
            "limit": {"default": 50, "type": "int"},
            "offset": {"default": 0, "type": "int"},
        },
    },
}
NET_OBJS_REQUIRED = ["net_objects"]
NET_OBJS_MUTUALLY_EXCLUSIVE = []
NET_OBJS_REQUIRED_TOGETHER = []
NET_OBJS_REQUIRED_IF = []
