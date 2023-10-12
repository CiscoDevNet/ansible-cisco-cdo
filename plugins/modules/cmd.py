#!/usr/bin/python
# -*- coding: utf-8 -*-
#
# Apache License v2.0+ (see LICENSE or https://www.apache.org/licenses/LICENSE-2.0)


from __future__ import absolute_import, division, print_function

__metaclass__ = type


DOCUMENTATION = r"""
---
module: cmd

short_description: Run arbitrary commands on an ASA or IOS device on Cisco Defense Orchestrator (CDO).

version_added: "1.2.0"

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
from ansible_collections.cisco.cdo.plugins.module_utils.errors import RetriesExceeded, CmdExecutionError
from ansible_collections.cisco.cdo.plugins.module_utils.query import CDOQuery
from ansible_collections.cisco.cdo.plugins.module_utils.common import gather_inventory, get_specific_device
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


def poll_cmd_execution(module_params: dict, http_session: requests.session, endpoint: str, transaction_id: str):
    poll_attempt = 0
    while True:
        if poll_attempt > module_params.get("retries"):
            raise (
                RetriesExceeded(
                    "Timeout waiting for the command(s) to execute on the device. Perhaps try raising "
                    "the retries or interval playbook values. "
                )
            )
        logger.debug(f"PAYLOAD: {CDOQuery.cli_executions_query(transaction_id)}")
        response = CDORequests.get(
            http_session,
            f"https://{endpoint}",
            path=f"{CDOAPI.CLI_EXECUTIONS.value}",
            query=CDOQuery.cli_executions_query(transaction_id),
        )
        logger.debug(f"data type: {type(response)}")
        logger.debug(f"POLLER-OUTPUT: {response}")
        if isinstance(response, list) and response:
            if response[0].get("executionState") == "DONE":
                return response[0].get("response")
            elif response[0].get("errorMsg"):
                raise CmdExecutionError(
                    response[0].get("errorMsg")
                )  # For example: If the device is not sync'd or unreachable
        sleep(module_params.get("interval"))
        poll_attempt += 1


def is_device_in_sync(device_info: dict) -> bool:
    if device_info.get("configState") != "SYNCED" or device_info.get("oobDetectionState") == "OOB_CHANGE_DETECTED":
        return False
    return True


def is_command_allowed_out_of_sync(module_params: dict) -> bool:
    """Returns true if all of the commands are in the allowed-out-of-sync list (See CDO Docs) If there is a command
    that is not allowed when the device is out of sync, return False"""
    allowed_commands = ["show", "ping", "traceroute", "vpn-sessiondb", "changeto", "dir", "write", "copy"]
    for command in module_params.get("cmd_list"):
        if list(filter(command.startswith, allowed_commands)) == []:
            return False
    return True


def run_cmd(module_params: dict, http_session: requests.session, endpoint: str) -> list:
    cmd_results = list()
    module_params["filter"] = module_params["device_name"]
    device_details = gather_inventory(module_params, http_session, endpoint)
    if not len(device_details):
        return DeviceNotFound
    logger.debug(f"Check status: {device_details}")

    for device in device_details:
        if not is_device_in_sync(device):
            if not is_command_allowed_out_of_sync(module_params):
                raise DeviceNotInSync(
                    "Device is not in a synced state. The only allowed commands are:"
                    "show, ping, traceroute, vpn-sessiondb, changeto, dir, write, copy"
                )

            return
    specific_device = get_specific_device(http_session, endpoint, device_details[0].get("uid"))
    logger.debug(f"cmd {module_params.get('cmd_list')}")
    # PLaybook could include commands that exceed 600 characters. Split into multiple api calls as needed
    command_list = split_max_command_length(module_params.get("cmd_list"))
    for commands in command_list:
        transaction_id = generate_uuid()
        payload = {
            "queueTriggerState": "INITIATE_CLI",
            "stateMachineContext": {
                "command": "\n".join(commands),
                "transactionId": transaction_id,
                "cliMacroUid": None,
            },
        }
        CDORequests.put(
            http_session,
            f"https://{endpoint}",
            path=f"{CDOAPI.ASA_CONFIG.value}/{specific_device.get('uid')}",
            data=payload,
        )
        cmd_results.append(poll_cmd_execution(module_params, http_session, endpoint, transaction_id=transaction_id))
    return "".join(output for output in cmd_results)  # return all output as a string


def is_sub_command(command: str) -> bool:
    """If the command starts with a space or tab, then it is a sub command of a parent command:
    e.g. 'object-group network foo' is a parent command while ' network-object object INSIDE-NET' is a sub-command of
    'object-group network foo'
    Return False if this is a parent command and true if this is a sub command
    """
    if not command.startswith(" ") and not command.startswith("\t"):
        return False
    return True


def split_max_command_length(command_list: list) -> list[list]:
    """The CDO API can take at most 600 characters per API call. Split the list of commands fed from the playbook into
    lists where the total number of characters from every line in the list add up to less than 600 characters,
    including the /n that will be added to each command."""
    # TODO: deal with multi-nested sub commands
    command_sets = list()  # return a list of lists
    command_set = list()  # the ephemeral list to add to the return list
    length = 0  # current number of chars in the command set
    top_level_command = ""  # The top level commands to track for splitting purposes

    for line in command_list:
        if not is_sub_command(line):
            top_level_command = line  # Save the top level command in case we need to split over multiple API calls
        length = length + len(line) + 2
        if length > 599:
            command_sets.append(command_set)  # Append the list of commands under 600 characters total
            command_set = list()  # reset the running list
            length = 0  # reset the character count
            if is_sub_command(line):
                command_set.append(top_level_command)  # Splitting a sub command so we need to re-issue top level cmd
            command_set.append(line)
        else:
            command_set.append(line)
    command_sets.append(command_set)
    return command_sets


def get_running_config(
    module_params: dict, http_session: requests.session, endpoint: str, extra_parameter="", all=False
):
    """Get the running config from the ASA.
    all=True: do a "show run all
    extra_parameter="| aaa": do a show run | aaa
    """
    show_run = f"show run all {extra_parameter}" if all else f"show run {extra_parameter}"
    module_params["cmd_list"] = [f"{show_run}".strip()]
    running_config = run_cmd(module_params, http_session, endpoint)
    return running_config


def get_access_list_names(module_params: dict, http_session: requests.session, endpoint: str) -> set:
    """Get the access-list names from the running config"""
    acls = get_running_config(module_params, http_session, endpoint, extra_parameter="access-list").split("\n")
    return set([line.split(" ")[1] for line in acls])


def execute_config(module_params: dict, http_session: requests.session, endpoint: str):
    results = ""
    for key, command_list in module_params.get("config").items():
        config = list()
        logger.debug(f"Processing key {key}")
        for line in command_list:
            config.append(line)
        module_params["cmd_list"] = config
        logger.debug(f"List of commands to run: { module_params['cmd_list']}")
        results = f"{results} {run_cmd(module_params, http_session, endpoint)}"
        logger.debug(f"run_cmd_result: {results}")
    sleep(5)
    return results


def load_config(module_params: dict, http_session: requests.session, endpoint: str):
    result = execute_config(module_params, http_session, endpoint)
    return result


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
        try:
            result["stdout"] = run_cmd(module.params.get("exec_command"), http_session, endpoint)
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

    elif module.params.get("load_config"):
        try:
            result["stdout"] = load_config(module.params.get("load_config"), http_session, endpoint)
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
