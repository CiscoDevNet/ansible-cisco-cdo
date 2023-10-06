#!/usr/bin/python
# -*- coding: utf-8 -*-
#
# Apache License v2.0+ (see LICENSE or https://www.apache.org/licenses/LICENSE-2.0)


from __future__ import absolute_import, division, print_function

__metaclass__ = type


DOCUMENTATION = r"""
---
module: deploy

short_description: Check for changes and deploy to devices (FTD, ASA, IOS devices) on Cisco Defense Orchestrator (CDO).

version_added: "1.0.3"

description: This module is to read inventory (FTD, ASA, IOS devices) on Cisco Defense Orchestrator (CDO).
"""

# fmt: off
import requests
import time
from time import sleep
from ansible_collections.cisco.cdo.plugins.module_utils.api_endpoints import CDOAPI
from ansible_collections.cisco.cdo.plugins.module_utils.api_requests import CDORegions, CDORequests
from ansible_collections.cisco.cdo.plugins.module_utils._version import __version__
from ansible_collections.cisco.cdo.plugins.module_utils.args_common import (
    CMD_ARGUMENT_SPEC,
    CMD_MUTUALLY_REQUIRED_ONE_OF,
    CMD_MUTUALLY_EXCLUSIVE,
    CMD_REQUIRED_IF
)
from ansible_collections.cisco.cdo.plugins.module_utils.query import CDOQuery
from ansible_collections.cisco.cdo.plugins.module_utils.common import gather_inventory
from ansible_collections.cisco.cdo.plugins.module_utils.errors import DeviceNotFound, TooManyMatches, APIError, CredentialsFailure
from ansible.module_utils.basic import AnsibleModule
# fmt: on

# fmt: off
# Remove for publishing....
import logging
logging.basicConfig()
logger = logging.getLogger('cmd')
fh = logging.FileHandler('/tmp/cmd.log')
fh.setLevel(logging.DEBUG)
logger.setLevel(logging.DEBUG)
logger.addHandler(fh)
logger.debug("Logger started......")
# fmt: on


def run_cmd(module_params: dict, http_session: requests.session, endpoint: str):
    # TODO: Call the run API point and return output from CLI command...
    pass


def main():
    result = dict(msg="", stdout="", stdout_lines=[], stderr="", stderr_lines=[], rc=0, failed=False, changed=False)
    module = AnsibleModule(
        argument_spec=CMD_ARGUMENT_SPEC,
        required_one_of=[CMD_MUTUALLY_REQUIRED_ONE_OF],
        mutually_exclusive=CMD_MUTUALLY_EXCLUSIVE,
        required_if=CMD_REQUIRED_IF,
    )

    logger.debug(f"Params: {module.params}")

    endpoint = CDORegions.get_endpoint(module.params.get("region"))
    http_session = CDORequests.create_session(module.params.get("api_key"), __version__)

    # Execute command(s) to specific device
    if module.params.get("exec_command"):
        logger.debug(f"Params: {module.params.get('exec_command')}")
        try:
            run_cmd(module.params.get("cmd"), http_session, endpoint)
        except (DeviceNotFound, TooManyMatches, APIError, CredentialsFailure) as e:
            result["stderr"] = f"ERROR: {e.message}"

    module.exit_json(**result)


if __name__ == "__main__":
    main()
