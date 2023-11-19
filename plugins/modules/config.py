# -*- coding: utf-8 -*-
#
# Apache License v2.0+ (see LICENSE or https://www.apache.org/licenses/LICENSE-2.0)


from __future__ import absolute_import, division, print_function

__metaclass__ = type


DOCUMENTATION = r"""
---
module: config

short_description: Return the current device config from Cisco Defense Orchestrator (CDO).

description: This module is to read device config (ASA and IOS devices) on Cisco Defense Orchestrator (CDO).

author: Aaron Hackney (@aaronhackney)
"""

# fmt: off
from ansible_collections.cisco.cdo.plugins.module_utils.api_requests import CDORegions, CDORequests
from ansible_collections.cisco.cdo.plugins.module_utils.config.config import Config
from ansible_collections.cisco.cdo.plugins.module_utils._version import __version__
from ansible_collections.cisco.cdo.plugins.module_utils.args_common import (
    CONFIG_ARGUMENT_SPEC,
    CONFIG_MUTUALLY_REQUIRED_ONE_OF,
    CONFIG_MUTUALLY_EXCLUSIVE,
    CONFIG_REQUIRED_IF
)
from ansible_collections.cisco.cdo.plugins.module_utils.errors import RetriesExceeded, CmdExecutionError
from ansible_collections.cisco.cdo.plugins.module_utils.errors import (
    DeviceNotFound,
    TooManyMatches,
    APIError,
    CredentialsFailure,
    DeviceNotInSync
)
from ansible.module_utils.basic import AnsibleModule
# fmt: on


# fmt: off
# Remove for publishing....
import logging
logging.basicConfig()
logger = logging.getLogger('config_module')
fh = logging.FileHandler('/tmp/config_module.log')
fh.setLevel(logging.DEBUG)
logger.setLevel(logging.DEBUG)
logger.addHandler(fh)
logger.debug("config_module.log logger started......")
# fmt: on


def main():
    result = dict(msg="", stdout="", stdout_lines=[], stderr="", stderr_lines=[], rc=0, failed=False, changed=False)
    module = AnsibleModule(
        argument_spec=CONFIG_ARGUMENT_SPEC,
        required_one_of=[CONFIG_MUTUALLY_REQUIRED_ONE_OF],
        mutually_exclusive=CONFIG_MUTUALLY_EXCLUSIVE,
        required_if=CONFIG_REQUIRED_IF,
    )
    endpoint = CDORegions[module.params.get("region")].value
    http_session = CDORequests.create_session(module.params.get("api_key"), __version__)

    try:
        if module.params.get("config"):
            config = Config(module.params.get("config"), http_session, endpoint)
            result["cdo"] = config.get_asa_configs()
            result["changed"] = False
    except (
        DeviceNotFound,
        TooManyMatches,
        APIError,
        CredentialsFailure,
        RetriesExceeded,
        CmdExecutionError,
        DeviceNotInSync,
    ) as e:
        result["stderr"] = f"ERROR: {e.message}"
    module.exit_json(**result)


if __name__ == "__main__":
    main()
