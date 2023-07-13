ADD_ASA_IOS_SPEC = {
    "api_key": {"required": True, "type": "str", "no_log": True},
    "region": {"default": "us", "choices": ["us", "eu", "apj"], "type": "str"},
    "add_asa_ios": {"type": "dict",
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
                    }},
}

ADD_FTD_SPEC = {
    "api_key": {"required": True, "type": "str", "no_log": True},
    "region": {"default": "us", "choices": ["us", "eu", "apj"], "type": "str"},
    "add_ftd": {"type": "dict",
                "options": {
                        "name": {"required": True, "type": "str"},
                        "is_virtual": {"default": False, "type": "bool"},
                        "onboard_method": {"default": "cli", "choices": ["cli", "ltp"], "type": "str"},
                        "access_control_policy": {"default": "Default Access Control Policy", "type": "str"},
                        "license": {
                            "type": "list",
                            "choices": ["BASE", "THREAT", "URLFilter", "MALWARE", "CARRIER", "PLUS", "APEX", "VPNOnly"]
                        },
                    "performance_tier": {
                            "choices": ["FTDv", "FTDv5", "FTDv10", "FTDv20", "FTDv30", "FTDv50", "FTDv100"],
                            "type": "str"
                        },
                    "retry": {"default": 10, "type": "int"},
                    "delay": {"default": 1, "type": "int"},
                    "serial": {"type": "str"},
                    "password": {"default": "", "type": "str"}
                }}
}

DELETE_SPEC = {
    "api_key": {"required": True, "type": "str", "no_log": True},
    "region": {"default": "us", "choices": ["us", "eu", "apj"], "type": "str"},
    "delete": {"type": "dict",
               "options": {
                   "filter": {"type": "str"},
                   "name": {"required": True, "type": "str"},
                   "device_type": {"required": True, "choices": ["asa", "ios", "ftd"], "type": "str"}
               }}
}

INVENTORY_ARGUMENT_SPEC = {
    "api_key": {"required": True, "type": "str", "no_log": True},
    "region": {"default": "us", "choices": ["us", "eu", "apj"], "type": "str"},
    "inventory": {"type": "dict",
                  "options": {
                          "filter": {"type": "str"},
                          "device_type": {"default": "all", "choices": ["all", "asa", "ios", "ftd", "fmc"]}
                  }}
}

REQUIRED_ONE_OF = ["inventory", "add_asa_ios", "add_ftd", "delete"]

MUTUALLY_EXCLUSIVE = []

REQUIRED_TOGETHER = []

REQUIRED_IF = []
