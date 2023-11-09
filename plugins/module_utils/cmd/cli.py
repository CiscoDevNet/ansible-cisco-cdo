# -*- coding: utf-8 -*-
#
# Apache License v2.0+ (see LICENSE or https://www.apache.org/licenses/LICENSE-2.0)

from __future__ import absolute_import, division, print_function

__metaclass__ = type

import requests
from time import sleep
from ansible_collections.cisco.cdo.plugins.module_utils.api_endpoints import CDOAPI
from ansible_collections.cisco.cdo.plugins.module_utils.api_requests import CDORequests
from ansible_collections.cisco.cdo.plugins.module_utils._version import __version__
from ansible_collections.cisco.cdo.plugins.module_utils.errors import RetriesExceeded, CmdExecutionError
from ansible_collections.cisco.cdo.plugins.module_utils.query import CDOQuery
from ansible_collections.cisco.cdo.plugins.module_utils.device_inventory.inventory import Inventory
from ansible_collections.cisco.cdo.plugins.module_utils.errors import (
    DeviceNotFound,
    TooManyMatches,
    DeviceNotInSync,
)


# fmt: off
# Remove for publishing....
import logging
logging.basicConfig()
logger = logging.getLogger('cli')
fh = logging.FileHandler('/tmp/cli.log')
fh.setLevel(logging.DEBUG)
logger.setLevel(logging.DEBUG)
logger.addHandler(fh)
logger.debug("Logger started cli.py......")
# fmt: on


class CLI:
    # TODO: Trigger OOB check before write operations
    # TODO: get running config and process it into needed parts
    # TODO: use an existing library to parse ASA config pieces
    def __init__(self, module_params: dict, http_session: requests.session, endpoint: str):
        self.module_params = module_params
        self.http_session = http_session
        self.endpoint = endpoint
        self.inventory_client = Inventory(module_params, http_session, endpoint)
        self.changed = False
        self.results = list()

    def poll_cmd_execution(self, transaction_id: str):
        """Wait for the cli commands to complete execution"""
        response = None
        poll_attempt = 0
        while True:
            if poll_attempt > self.module_params.get("retries"):
                raise (
                    RetriesExceeded(
                        "Timeout waiting for the command(s) to execute on the device. Perhaps try raising "
                        "the retries or interval values. "
                    )
                )
            response = CDORequests.get(
                self.http_session,
                f"https://{self.endpoint}",
                path=f"{CDOAPI.CLI_EXECUTIONS.value}",
                query=CDOQuery.cli_executions_query(transaction_id),
            )
            if isinstance(response, list) and response:
                if response[0].get("executionState") == "DONE":
                    if not response[0].get("response"):
                        return
                    else:
                        return response[0].get("response")
                elif response[0].get("errorMsg"):
                    raise CmdExecutionError(
                        response[0].get("errorMsg")
                    )  # For example: If the device is not sync'd or unreachable
            sleep(self.module_params.get("interval"))
            poll_attempt += 1

    def get_device_details(self) -> dict:
        """Get the device details from CDO inventory"""
        self.module_params["filter"] = self.module_params["device_name"]
        device_details = self.inventory_client.gather_inventory()
        return device_details

    def is_command_allowed_out_of_sync(self) -> bool:
        """Returns true if all of the commands are in the allowed-out-of-sync list (See CDO Docs) If there is a command
        that is not allowed when the device is out of sync, return False"""
        allowed_commands = ["show", "ping", "traceroute", "vpn-sessiondb", "changeto", "dir", "write", "copy"]
        for command in self.module_params.get("cmd_list"):
            if list(filter(command.startswith, allowed_commands)) == []:
                return False
        return True

    def run_cmd(self) -> str:
        """
        Run the commands queued in the class attribute self.module_params["cmd_list"]
        Note that the ASA/CDO CLI API can only take up to 600 chars at a time, so in
        this method, we split the commands into less than 600 character chunks and send
        them all unit the entire cmd_list has been executed.
        """
        cmd_results = list()
        device_details = self.get_device_details()
        if not device_details:
            raise DeviceNotFound(f'Device {self.module_params["device_name"]} not found in CDO inventory')
        elif len(device_details) != 1:
            raise TooManyMatches(
                f'Device {self.module_params["device_name"]} matched more than 1 device in CDO inventory'
            )
        if not self.inventory_client.is_device_in_sync(
            device_details[0]
        ):  # Out of sync devices have a restricted command set
            if not self.is_command_allowed_out_of_sync():  # check the command is in the restricted command set
                raise DeviceNotInSync(
                    "Device is not in a synced state. The only allowed commands are:"
                    "show, ping, traceroute, vpn-sessiondb, changeto, dir, write, copy"
                )
        specific_device = self.inventory_client.get_specific_device(device_details[0].get("uid"))
        split_cmd_list = self.split_max_command_length(self.module_params.get("cmd_list"))  # API has max 600 char limit

        for commands in split_cmd_list:
            transaction_id = self.inventory_client.generate_uuid()
            payload = {
                "queueTriggerState": "INITIATE_CLI",
                "stateMachineContext": {
                    "command": "\n".join(commands),
                    "transactionId": transaction_id,
                    "cliMacroUid": None,
                },
            }
            CDORequests.put(
                self.http_session,
                f"https://{self.endpoint}",
                path=f"{CDOAPI.ASA_CONFIG.value}/{specific_device.get('uid')}",
                data=payload,
            )
            results = self.poll_cmd_execution(transaction_id)
            if results:
                cmd_results.extend(results.split("\n"))
        return cmd_results

    def is_sub_command(self, command: str) -> bool:
        """If the command starts with a space or tab, then it is a sub command of a parent command:
        e.g. 'object-group network foo' is a parent command while ' network-object object INSIDE-NET' is a sub-command of
        'object-group network foo'
        Return False if this is a parent command and true if this is a sub command
        """
        if not command.startswith(" ") and not command.startswith("\t"):
            return False
        return True

    def split_max_command_length(self, command_list: list) -> list[list]:
        """The CDO API can take at most 600 characters per API call. Split the list of commands fed from the playbook into
        lists where the total number of characters from every line in the list add up to less than 600 characters,
        including the /n that will be added to each command."""
        # TODO: deal with multi-nested sub commands
        command_sets = list()  # return a list of lists
        command_set = list()  # the ephemeral list to add to the return list
        length = 0  # current number of chars in the command set
        top_level_command = ""  # The top level commands to track for splitting purposes
        for line in command_list:
            if not self.is_sub_command(line):
                top_level_command = line  # Save the top level command in case we need to split over multiple API calls
            length = length + len(line) + 2
            if length > 599:
                command_sets.append(
                    command_set
                )  # Append list of commands < 600 characters total not including this line
                command_set = list()  # reset the running list
                length = 0  # reset the character count
                command_set.append(top_level_command) if self.is_sub_command(line) else ""
                command_set.append(line)
            else:
                command_set.append(line)
        command_sets.append(command_set) if command_set else ""
        return command_sets

    def get_running_config(self, extra_parameter="", all=False):
        """Get the running config from the ASA. all=True: do a "show run all extra_parameter="| aaa": do a show run | aaa"""
        self.module_params["cmd_list"] = [f"show run all {extra_parameter}" if all else f"show run {extra_parameter}"]
        running_config = self.run_cmd()
        return running_config
