#!/usr/bin/python
# -*- coding: utf-8 -*-
#
# Apache License v2.0+ (see LICENSE or https://www.apache.org/licenses/LICENSE-2.0)


from __future__ import absolute_import, division, print_function

__metaclass__ = type

# fmt: off
# Remove for publishing....
import logging
logging.basicConfig()
logger = logging.getLogger('inventory')
fh = logging.FileHandler('/tmp/inventory.log')
fh.setLevel(logging.DEBUG)
logger.setLevel(logging.DEBUG)
logger.addHandler(fh)
logger.debug("Logger started......")
# fmt: on

DOCUMENTATION = r"""
---
module: inventory

short_description: This module is to read inventory (FTD, ASA, IOS devices) on Cisco Defense Orchestrator (CDO).

version_added: "1.0.0"

description: This module is to read inventory (FTD, ASA, IOS devices) on Cisco Defense Orchestrator (CDO).
options:
    api_key:
        description:
            - API key for the tenant on which we wish to operate
        required: true
        type: str
    region:
        description:
            - The region where the CDO tenant exists
        choices: [us, eu, apj]
        default: us
        required: true
        type: str
    inventory:
        description:
            - Return a dictionary of json device objects in the current tenant's inventory
        required: false
        type: dict
author:
    - Aaron Hackney (@aaronhackney)
requirements:
  - pycryptodome
  - requests

"""

EXAMPLES = r"""
- name: Get device inventory details
  hosts: localhost
  tasks:
    - name: Get the CDO inventory for this tenant
      cisco.cdo.cdo_inventory:
        api_key: "{{ lookup('ansible.builtin.env', 'CDO_API_KEY') }}"
        region: "us"
        inventory:
          device_type: "all"
      register: inventory

    - name: Print All Results for all devices, all fields
      ansible.builtin.debug:
        msg:
          "{{ inventory.stdout }}"
"""

# fmt: off
from ansible_collections.cisco.cdo.plugins.module_utils.requests import CDORegions, CDORequests
from ansible_collections.cisco.cdo.plugins.module_utils._version import __version__
from ansible_collections.cisco.cdo.plugins.module_utils.common import gather_inventory
from ansible_collections.cisco.cdo.plugins.module_utils.inventory.ftd import add_ftd
from ansible_collections.cisco.cdo.plugins.module_utils.inventory.asa import add_asa_ios
from ansible_collections.cisco.cdo.plugins.module_utils.inventory.delete import delete_device
from ansible_collections.cisco.cdo.plugins.module_utils.errors import (
    DeviceNotFound,
    AddDeviceFailure,
    DuplicateObject,
    ObjectNotFound,
    SDCNotFound,
    InvalidCertificate,
    DeviceUnreachable,
    APIError,
    CredentialsFailure
)
from ansible_collections.cisco.cdo.plugins.module_utils.args_common import (
    INVENTORY_ARGUMENT_SPEC,
    INVENTORY_REQUIRED_ONE_OF,
    INVENTORY_MUTUALLY_EXCLUSIVE,
    INVENTORY_REQUIRED_IF
)
from ansible.module_utils.basic import AnsibleModule

# fmt: on


def main():
    result = dict(msg="", stdout="", stdout_lines=[], stderr="", stderr_lines=[], rc=0, failed=False, changed=False)
    module = AnsibleModule(
        argument_spec=INVENTORY_ARGUMENT_SPEC,
        required_one_of=[INVENTORY_REQUIRED_ONE_OF],
        mutually_exclusive=INVENTORY_MUTUALLY_EXCLUSIVE,
        required_if=INVENTORY_REQUIRED_IF,
    )
    endpoint = CDORegions.get_endpoint(module.params.get("region"))
    http_session = CDORequests.create_session(module.params.get("api_key"), __version__)

    if module.params.get("gather"):
        result["stdout"] = gather_inventory(module.params.get("gather"), http_session, endpoint)
        result["changed"] = False
    if module.params.get("add"):
        if module.params.get("add", {}).get("ftd"):
            try:
                result["stdout"] = add_ftd(module.params.get("add", {}).get("ftd"), http_session, endpoint)
                result["changed"] = True
            except AddDeviceFailure as e:
                result["stderr"] = f"ERROR: {e.message}"
            except DuplicateObject as e:
                result["stderr"] = f"ERROR: {e.message}"
            except DeviceNotFound as e:
                result["stderr"] = f"ERROR: {e.message}"
            except ObjectNotFound as e:
                result["stderr"] = f"ERROR: {e.message}"
        if module.params.get("add", {}).get("asa_ios"):
            try:
                result["stdout"] = add_asa_ios(module.params.get("add", {}).get("asa_ios"), http_session, endpoint)
                result["changed"] = True
            except SDCNotFound as e:
                result["stderr"] = f"ERROR: {e.message}"
            except InvalidCertificate as e:
                result["stderr"] = f"ERROR: {e.message}"
            except DeviceUnreachable as e:
                result["stderr"] = f"ERROR: {e.message}"
            except CredentialsFailure as e:
                result["stderr"] = f"ERROR: {e.message}"
            except DuplicateObject as e:
                result["stderr"] = f"ERROR: {e.message}"
            except APIError as e:
                result["stderr"] = f"ERROR: {e.message}"
    if module.params.get("delete"):
        # TODO: add error handling for delete
        logger.debug(f"Deleting device {module.params.get('delete')}")
        result["stdout"] = delete_device(module.params.get("delete"), http_session, endpoint)
        result["changed"] = True
    module.exit_json(**result)


if __name__ == "__main__":
    main()
