# -*- coding: utf-8 -*-
#
# Apache License v2.0+ (see LICENSE or https://www.apache.org/licenses/LICENSE-2.0)


from __future__ import absolute_import, division, print_function

__metaclass__ = type

DOCUMENTATION = r"""
---
module: inventory

short_description: This module is to read inventory (FTD, ASA, IOS devices) on Cisco Defense Orchestrator (CDO).

version_added: "1.0.0"

description: This module is to read inventory (FTD, ASA, IOS devices) on Cisco Defense Orchestrator (CDO).
options:
    api_key:
        type: str
        required: true
        no_log: true
    region:
        type: str
        choices: [us, eu, apj]
        default: us
    add:
        ftd:
            device_name:
                type: str
                required: True
            onboard_method:
                type: str
                choices: [ltp, cli]
                default: cli
            access_control_policy:
                type: str
                default: Default Access Control Policy
            is_virtual:
                default: False
                type: bool
            license:
                type: list
                choices: [BASE, THREAT, URLFilter, MALWARE, CARRIER, PLUS, APEX, VPNOnly]
                default: [BASE]
            performance_tier:
                type: str
                choices: [FTDv, FTDv5, FTDv10, FTDv20, FTDv30, FTDv50, FTDv100]
            retry:
                type: int
                default: 10
            delay:
                type: int
                default: 1
            serial:
                type: str
            password:
                type: str
        asa_ios:
            device_name:
                type: str
                required: True
            ipv4:
                type: str
            port:
                type: int
                default: 443
            sdc:
                type: str
            username:
                type: str
            password:
                type: str
            ignore_cert:
                type: bool
                default: False
            device_type:
                type: str
                choices: [asa, ios]
                default: asa
            retry:
                type: int
                default: 10
            delay:
                type: int
                default: 1
    delete:
        device_name:
            type: str
            required: True
        device_type:
            type: str
            required: True
            choices: [asa, ios, ftd]

author:
    - Aaron Hackney (@aaronhackney)
requirements:
  - pycryptodome
  - requests

"""

EXAMPLES = r"""
---
- name: Get device inventory details
  hosts: localhost
  tasks:
    - name: Get the CDO inventory for this tenant
      cisco.cdo.device_inventory:
        api_key: "{{ lookup('ansible.builtin.env', 'CDO_API_KEY') }}"
        region: "us"
        gather:
          device_type: "all"
      register: inventory
      failed_when: (inventory.stderr is defined) and (inventory.stderr | length > 0)

    - name: Print All Results for all devices, all fields
      ansible.builtin.debug:
        msg:
          "{{ inventory.stdout }}"

- name: Add FTD CDO inventory via CLI or LTP
  hosts: all
  connection: local
  tasks:
    - name: Add FTD to CDO and cdFMC via CLI or LTP
      when: hostvars[inventory_hostname].device_type == "ftd"
      cisco.cdo.device_inventory:
        api_key: "{{ lookup('ansible.builtin.env', 'CDO_API_KEY') }}"
        region: "{{ lookup('ansible.builtin.env', 'CDO_REGION') }}"
        add:
          ftd:
            device_name: "{{ inventory_hostname }}"
            onboard_method: "{{ hostvars[inventory_hostname].onboard_method }}"
            access_control_policy: "{{ hostvars[inventory_hostname].access_control_policy }}"
            is_virtual: "{{ hostvars[inventory_hostname].is_virtual }}"
            performance_tier: "{{ hostvars[inventory_hostname].performance_tier }}"
            license: "{{ hostvars[inventory_hostname].license }}"
            serial: "{{ hostvars[inventory_hostname].serial | default(omit) }}"
      register: added_device
      failed_when: (added_device.stderr is defined) and (added_device.stderr | length > 0)

    - name: Print CLI FTD results
      when: added_device.stdout['metadata'] is defined and hostvars[inventory_hostname].device_type == "ftd"
      ansible.builtin.debug:
        msg:
          "{{ added_device.stdout['metadata']['generatedCommand'] }}"

    - name: Print LTP FTD results
      when: added_device.stdout['metadata'] is not defined and hostvars[inventory_hostname].device_type == "ftd"
      ansible.builtin.debug:
        msg:
          "{{ added_device.stdout }}"

- name: Add ansible inventory to CDO
  hosts: all
  connection: local
  tasks:
    - name: Add ASA to CDO
      when:  hostvars[inventory_hostname].device_type == "asa" or hostvars[inventory_hostname].device_type == "ios"
      cisco.cdo.device_inventory:
        api_key: "{{ lookup('ansible.builtin.env', 'CDO_API_KEY') }}"
        region: "{{ lookup('ansible.builtin.env', 'CDO_REGION') }}"
        add:
          asa_ios:
            sdc: "{{ hostvars[inventory_hostname].sdc if hostvars[inventory_hostname].sdc is defined }}"
            device_name: "{{ inventory_hostname }}"
            ipv4: "{{ hostvars[inventory_hostname].ipv4 }}"
            mgmt_port: "{{ hostvars[inventory_hostname].mgmt_port }}"
            device_type: "{{ hostvars[inventory_hostname].device_type }}"
            username: "{{ hostvars[inventory_hostname].username }}"
            password: "{{ hostvars[inventory_hostname].password }}"
            ignore_cert: "{{ hostvars[inventory_hostname].ignore_cert }}"
      register: added_device
      failed_when: (added_device.stderr is defined) and (added_device.stderr | length > 0)

    - name: Print results
      ansible.builtin.debug:
        msg: "{{ added_device }}"

- name: Delete devices from CDO inventory
  hosts: all
  connection: local
  tasks:
    - name: Delete devices from CDO inventory
      cisco.cdo.device_inventory:
        api_key: "{{ lookup('ansible.builtin.env', 'CDO_API_KEY') }}"
        region: "{{ lookup('ansible.builtin.env', 'CDO_REGION') }}"
        delete:
          device_name: "{{ inventory_hostname }}"
          device_type:  "{{ hostvars[inventory_hostname].device_type }}"
      register: deleted_device
      failed_when: (deleted_device.stderr is defined) and (deleted_device.stderr | length > 0)

    - name: Print results
      ansible.builtin.debug:
        msg:
          "{{ deleted_device }}"
"""

# fmt: off
from ansible_collections.cisco.cdo.plugins.module_utils.api_requests import CDORegions, CDORequests
from ansible_collections.cisco.cdo.plugins.module_utils._version import __version__
from ansible_collections.cisco.cdo.plugins.module_utils.device_inventory.ftd import FTD_Inventory
from ansible_collections.cisco.cdo.plugins.module_utils.device_inventory.asa import ASA_IOS_Inventory
from ansible_collections.cisco.cdo.plugins.module_utils.device_inventory.delete import DeleteInventory
from ansible_collections.cisco.cdo.plugins.module_utils.device_inventory.inventory import Inventory
from ansible_collections.cisco.cdo.plugins.module_utils.errors import (
    DeviceNotFound,
    AddDeviceFailure,
    DuplicateObject,
    ObjectNotFound,
    SDCNotFound,
    InvalidCertificate,
    DeviceUnreachable,
    APIError,
    CredentialsFailure,
    TooManyMatches
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
    endpoint = CDORegions[module.params.get("region")].value
    http_session = CDORequests.create_session(module.params.get("api_key"), __version__)
    # Get inventory from CDO and return a list of dict(s) - Devices and attributes
    if module.params.get("gather"):
        try:
            inventory_client = Inventory(module.params.get("gather"), http_session, endpoint)
            result["stdout"] = inventory_client.gather_inventory()
            result["changed"] = False
        except (CredentialsFailure, APIError) as e:
            result["stderr"] = f"ERROR: {e.message}"
    # Add devices to CDO inventory and return a json dictionary of the new device attributes
    if module.params.get("add"):
        if module.params.get("add", {}).get("ftd"):
            ftd_client = FTD_Inventory(module.params.get("add", {}).get("ftd"), http_session, endpoint)
            try:
                result["stdout"] = ftd_client.add_ftd()
                result["changed"] = True
            except DuplicateObject as e:
                result["stdout"] = f"Device Not added: {e.message}"
                result["changed"] = False
                result["failed"] = False
            except (AddDeviceFailure, DeviceNotFound, ObjectNotFound, CredentialsFailure) as e:
                result["stderr"] = f"ERROR: {e.message}"
                result["changed"] = False
                result["failed"] = True
        if module.params.get("add", {}).get("asa_ios"):
            asa_ios_client = ASA_IOS_Inventory(module.params.get("add", {}).get("asa_ios"), http_session, endpoint)
            try:
                result["stdout"] = asa_ios_client.add_asa_ios()
                result["changed"] = True
            except DuplicateObject as e:
                result["stdout"] = f"Device Not added: {e.message}"
                result["changed"] = False
                result["failed"] = False
            except (SDCNotFound, InvalidCertificate, DeviceUnreachable, CredentialsFailure, APIError) as e:
                result["stderr"] = f"ERROR: {e.message}"
                result["changed"] = False
                result["failed"] = True
    # Delete an ASA, FTD, or IOS device from CDO/cdFMC
    # TODO: not found should not fail....
    if module.params.get("delete"):
        try:
            delete_client = DeleteInventory(module.params.get("delete"), http_session, endpoint)
            delete_client.delete_device()
            result["changed"] = True
        except (DeviceNotFound, TooManyMatches) as e:
            result["stderr"] = f"ERROR: {e.message}"

    module.exit_json(**result)


if __name__ == "__main__":
    main()
