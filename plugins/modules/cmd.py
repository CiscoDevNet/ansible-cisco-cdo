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
import uuid
import requests
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
from ansible_collections.cisco.cdo.plugins.module_utils.common import gather_inventory, get_specific_device
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


def generate_uuid():
    raw_uuid = uuid.uuid4().hex
    return f"{raw_uuid[0:8]}-{raw_uuid[8:12]}-{raw_uuid[12:16]}-{raw_uuid[16:20]}-{raw_uuid[20:]}"


def poll_cmd_execution(module_params: dict, http_session: requests.session, endpoint: str, trasaction_id: str):
    # TODO: Set number of times to poll
    # TODO: Set pause between polls
    logger.debug("Entered the poller...")
    logger.debug(f"Transaction ID: {trasaction_id}")
    while True:
        query = {
            "q": f"transactionId:{trasaction_id}",
            "resolve": (
                "[cli/executions.{createdDate,command,jobUid,deviceUid,transactionId,deviceType,deviceName,"
                "responseHash,executionState,errorMsg}]"
            ),
        }
        response = CDORequests.get(
            http_session, f"https://{endpoint}", path=f"{CDOAPI.CLI_EXECUTIONS.value}", query=query
        )

        logger.debug(f"Polling Response: {response}")
        if response.get("executionState") == "DONE":
            logger.debug(f"Execution State is Done!!")
            break
        elif response.get("errorMsg"):
            # TODO: Get example of an error and raise the error
            # For example: If the device is not sync'd or is unreachable
            break


def run_cmd(module_params: dict, http_session: requests.session, endpoint: str):
    module_params["filter"] = module_params["device_name"]
    device_details = gather_inventory(module_params, http_session, endpoint)
    if not len(device_details):
        return DeviceNotFound

    specific_device = get_specific_device(http_session, endpoint, device_details[0].get("uid"))
    commands = "\n".join(module_params.get("cmd_list"))
    transaction_id = generate_uuid()
    payload = {
        "queueTriggerState": "INITIATE_CLI",
        "stateMachineContext": {
            "command": commands,
            "transactionId": transaction_id,
            "cliMacroUid": None,
        },
    }

    result = CDORequests.put(
        http_session,
        f"https://{endpoint}",
        path=f"{CDOAPI.ASA_CONFIG.value}/{specific_device.get('uid')}",
        data=payload,
    )
    logger.debug(f"PUT Returns: {result}")
    poll_cmd_execution(module_params, http_session, endpoint, trasaction_id=transaction_id)


def main():
    result = dict(msg="", stdout="", stdout_lines=[], stderr="", stderr_lines=[], rc=0, failed=False, changed=False)
    module = AnsibleModule(
        argument_spec=CMD_ARGUMENT_SPEC,
        required_one_of=[CMD_MUTUALLY_REQUIRED_ONE_OF],
        mutually_exclusive=CMD_MUTUALLY_EXCLUSIVE,
        required_if=CMD_REQUIRED_IF,
    )

    endpoint = CDORegions.get_endpoint(module.params.get("region"))
    http_session = CDORequests.create_session(module.params.get("api_key"), __version__)

    # Execute command(s) to specific device
    if module.params.get("exec_command"):
        logger.debug(f"Params: {module.params.get('exec_command')}")
        try:
            run_cmd(module.params.get("exec_command"), http_session, endpoint)
        except (DeviceNotFound, TooManyMatches, APIError, CredentialsFailure) as e:
            result["stderr"] = f"ERROR: {e.message}"

    module.exit_json(**result)


if __name__ == "__main__":
    main()
