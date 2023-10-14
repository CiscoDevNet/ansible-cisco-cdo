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
from ansible_collections.cisco.cdo.plugins.module_utils.common import (
    gather_inventory,
    get_specific_device,
    is_device_in_sync,
    generate_uuid
)
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
        response = CDORequests.get(
            http_session,
            f"https://{endpoint}",
            path=f"{CDOAPI.CLI_EXECUTIONS.value}",
            query=CDOQuery.cli_executions_query(transaction_id),
        )
        if isinstance(response, list) and response:
            if response[0].get("executionState") == "DONE":
                return response[0].get("response")
            elif response[0].get("errorMsg"):
                raise CmdExecutionError(
                    response[0].get("errorMsg")
                )  # For example: If the device is not sync'd or unreachable
        sleep(module_params.get("interval"))
        poll_attempt += 1


def is_command_allowed_out_of_sync(module_params: dict) -> bool:
    """Returns true if all of the commands are in the allowed-out-of-sync list (See CDO Docs) If there is a command
    that is not allowed when the device is out of sync, return False"""
    allowed_commands = ["show", "ping", "traceroute", "vpn-sessiondb", "changeto", "dir", "write", "copy"]
    for command in module_params.get("cmd_list"):
        if list(filter(command.startswith, allowed_commands)) == []:
            return False
    return True


def get_device_details(module_params: dict, http_session: requests.session, endpoint: str) -> dict:
    """Get the device details from CDO inventory"""
    module_params["filter"] = module_params["device_name"]
    device_details = gather_inventory(module_params, http_session, endpoint)
    return device_details


def run_cmd(module_params: dict, http_session: requests.session, endpoint: str) -> str:
    cmd_results = list()
    device_details = get_device_details(module_params, http_session, endpoint)
    if not device_details:
        raise DeviceNotFound(f'Device {module_params["device_name"]} not found in CDO inventory')
    elif len(device_details) != 1:
        raise TooManyMatches(f'Device {module_params["device_name"]} matched more than 1 device in CDO inventory')
    if not is_device_in_sync(device_details[0]):  # Out of sync devices have a restricted command set
        if not is_command_allowed_out_of_sync(module_params):  # check the command is in the restricted command set
            raise DeviceNotInSync(
                "Device is not in a synced state. The only allowed commands are:"
                "show, ping, traceroute, vpn-sessiondb, changeto, dir, write, copy"
            )
    specific_device = get_specific_device(http_session, endpoint, device_details[0].get("uid"))
    split_cmd_list = split_max_command_length(module_params.get("cmd_list"))  # API has max 600 char limit
    for commands in split_cmd_list:
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
            command_set.append(top_level_command) if is_sub_command(line) else None
            # if is_sub_command(line):
            #     command_set.append(top_level_command)  # Splitting a sub command so we need to re-issue top level cmd
            command_set.append(line)
        else:
            command_set.append(line)
    command_sets.append(command_set)
    return command_sets


def get_running_config(
    module_params: dict, http_session: requests.session, endpoint: str, extra_parameter="", all=False
):
    """Get the running config from the ASA. all=True: do a "show run all extra_parameter="| aaa": do a show run | aaa"""
    module_params["cmd_list"] = [f"show run all {extra_parameter}" if all else f"show run {extra_parameter}"]
    # module_params["cmd_list"] = [f"{show_run}".strip()]
    running_config = run_cmd(module_params, http_session, endpoint)
    return running_config


def load_config(module_params: dict, http_session: requests.session, endpoint: str):
    results = ""
    for key, command_list in module_params.get("config").items():
        config = list()
        for line in command_list:
            config.append(line)
        module_params["cmd_list"] = config
        results = f"{results} {run_cmd(module_params, http_session, endpoint)}"
        return results


def clear_config_access_list(module_params: dict, http_session: requests.session, endpoint: str, command):
    # TODO normalize and send in one command and don't loop over each line....
    """Completely remove access-lists from the running config"""
    acls = get_running_config(module_params, http_session, endpoint, extra_parameter="access-list").split("\n")
    access_policy_list = set([line.split(" ")[1] for line in acls])
    if not access_policy_list:
        return
    if command.split(" ")[3] in access_policy_list:  # Extract the policy name from the clear config cmd
        module_params["cmd_list"] = [command]
        results = run_cmd(module_params, http_session, endpoint)
        if not results:
            results = f"access-list {command.split(' ')[3]} deleted"
    else:
        return f"access-list {command.split(' ')[3]} not found in running config - skipping..."
    return results


def clear_config_interfaces(module_params: dict, http_session: requests.session, endpoint: str, commands: list):
    """Reset interface settings to factory default"""
    interface_list = get_running_config(
        module_params, http_session, endpoint, extra_parameter="interface | i interface"
    ).split("\n")
    clear_interface_list = [command.split(" ", 2)[2] for command in commands]  # get "interface [name]"
    does_not_exist = list(set(clear_interface_list).difference(interface_list))  # These interfaces don't exist
    for interface in does_not_exist:
        [commands.remove(command) for command in commands if command.endswith(interface)]
    module_params["cmd_list"] = commands
    results = run_cmd(module_params, http_session, endpoint)
    return f"{results} Completed: {commands} - Interface(s) not found on device: {does_not_exist}"


def clear_config(module_params: dict, http_session: requests.session, endpoint: str) -> bool:
    """There are certain 'clear config' commands that will cause a failure. For example, if we try and 'clear config' a
    specific object like an access-list that does not exist, an error is thrown and the api call is aborted,so in those
    cases, do a sanity check to make sure that they exist before we attempt to delete them"""
    results = list()
    if module_params.get("access_lists"):
        for current_command in module_params.get("access_lists"):
            results.append(clear_config_access_list(module_params, http_session, endpoint, current_command))
    if module_params.get("interfaces"):
        # for current_command in module_params.get("interfaces"):
        results.append(clear_config_interfaces(module_params, http_session, endpoint, module_params.get("interfaces")))
    # TODO: other clear config commands to come (like objects and object-groups)
    return results


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
    try:
        if module.params.get("exec_command"):
            result["stdout"] = run_cmd(module.params.get("exec_command"), http_session, endpoint)
        elif module.params.get("load_config"):
            result["stdout"] = load_config(module.params.get("load_config"), http_session, endpoint)
        elif module.params.get("clear_config"):
            result["stdout"] = clear_config(module.params.get("clear_config"), http_session, endpoint)
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
