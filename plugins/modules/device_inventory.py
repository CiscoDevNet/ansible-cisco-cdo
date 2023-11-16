# -*- coding: utf-8 -*-
#
# Apache License v2.0+ (see LICENSE or https://www.apache.org/licenses/LICENSE-2.0)


from __future__ import absolute_import, division, print_function

__metaclass__ = type

DOCUMENTATION = r"""
module: device_inventory
short_description: >-
  This module is to read, add, and delete inventory (FTD, ASA, IOS devices) on
  Cisco Defense Orchestrator (CDO).
description: >-
  This module is to read, add, and delete inventory (FTD, ASA, IOS devices) on
  Cisco Defense Orchestrator (CDO).
author: Aaron Hackney (@aaronhackney)
requirements:
  - pycryptodome
  - requests
options:
  api_key:
    description: This is the CDO tenant's API token.
    type: str
    required: true
  region:
    description: This is the CDO region where the tenant exists.
    type: str
    choices:
      - us
      - eu
      - apj
    default: us
  gather:
    description: >-
      This option gathers inventory information from CDO and returns things like
      serial number, code version, uptime, etc.
    type: dict
    suboptions:
      filter:
        description: Filter the inventory based on a device's name or ipv4 address
        type: str
      device_type:
        description: The types of devices to gather from inventory
        type: str
        choices:
          - all
          - asa
          - ios
          - ftd
          - fmc
        default: all
  add:
    description: 'This option onboards an FTD, ASA, or IOS device to be managed by CDO'
    type: dict
    options:
      ftd:
        description: Define an FTD device to onboard
        type: dict
        options:
          device_name:
            description: Add a device to CDO and give it this display name
            type: str
            required: true
          onboard_method:
            description: Onboard the FTD using the traditional CLI or via LTP
            type: str
            choices:
              - ltp
              - cli
            default: cli
          access_control_policy:
            description: >-
              The access-control-policy from FMC to apply to the device at the
              time of onboarding
            type: str
            default: Default Access Control Policy
          is_virtual:
            description: 'If this is a virtual FTD, set this to true'
            default: false
            type: bool
          license:
            description: >-
              Provide a list of license entitlements to apply to the device. Can
              be changed later.
            type: list
            elements: str
            choices:
              - BASE
              - THREAT
              - URLFilter
              - MALWARE
              - CARRIER
              - PLUS
              - APEX
              - VPNOnly
            default:
              - BASE
          performance_tier:
            description: 'If this is an FTDv, select a performance tier'
            type: str
            choices:
              - FTDv
              - FTDv5
              - FTDv10
              - FTDv20
              - FTDv30
              - FTDv50
              - FTDv100
          retry:
            description: >-
              While waiting for the device to be added to CDO, retry this many
              times before giving up and failing.
            type: int
            default: 10
          delay:
            description: The amount of time to wait before retrying (See retry above)
            type: int
            default: 1
          serial:
            description: >-
              If the LTP onboarding method is used, we must provide a serial
              number
            type: str
          password:
            description: >-
              If the LTP onboarding method is used and the device has never been
              logged into we must provide a new admin password. Note that this
              needs to meet password complexity requirements.
            type: str
      asa_ios:
        description: Define an FTD device to onboard
        type: dict
        options:
          device_name:
            description: Add a device to CDO and give it this display name
            type: str
            required: true
          ipv4:
            description: >-
              The ip address that the SDC will use to communicate with the SDC.
              Usually the management interface ip address.
            type: str
            required: true
          mgmt_port:
            description: >-
              The TCP port on which the ASDM interface on the ASA listens. 443
              is the default.
            type: int
            default: 443
          sdc:
            description: >-
              The exact name of the SDC that will communicate with this ASA.
              This name can be found in CDO under Tools & Services --> Secure
              Connectors
            type: str
            required: true
          username:
            description: The admin username used to log into the ASA
            type: str
            required: true
          password:
            description: The admin password for the above username used to log into the ASA
            type: str
            required: true
          ignore_cert:
            description: >-
              If the ASA ASDM interface has an expired, self-signed, or invalid
              certificate, onboard it anyway (RISK!)
            type: bool
            default: false
          device_type:
            description: 'The type of device to onboard, an ASA or an IOS device'
            type: str
            choices:
              - asa
              - ios
            default: asa
          retry:
            description: >-
              While waiting for the device to be added to CDO, retry this many
              times before giving up and failing.
            type: int
            default: 10
          delay:
            description: The amount of time to wait before retrying (See retry above)
            type: int
            default: 1
  delete:
    description: >-
      This option removes an FTD, ASA, or IOS device from CDO and cdFMC if
      relevant.
    type: dict
    options:
      device_name:
        description: 'The type of device to delete [ASA, IOS, FTD]'
        type: str
        required: true
      device_type:
        description: The name of the device in CDO inventory to delete
        type: str
        required: true
        choices:
          - asa
          - ios
          - ftd

"""

EXAMPLES = r"""
---
- name: CDO Inventory operations
  hosts: all
  connection: local
  tasks:

- name: Get device inventory details
  hosts: localhost
  tasks:
    - name: Get the CDO inventory for this tenant
      cisco.cdo.device_inventory:
        api_key: "{{ lookup('ansible.builtin.env', 'CDO_API_KEY') }}"
        region: "us"
        gather:
          device_type: "all"

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

- name: Add ansible inventory to CDO
  hosts: all
  connection: local
  tasks:
    - name: Add ASA to CDO
      when: hostvars[inventory_hostname].device_type == "asa" or hostvars[inventory_hostname].device_type == "ios"
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
          device_type: "{{ hostvars[inventory_hostname].device_type }}"
"""

# fmt: off
import json
from ansible_collections.cisco.cdo.plugins.module_utils.api_requests import CDORegions, CDORequests
from ansible_collections.cisco.cdo.plugins.module_utils._version import __version__
from ansible_collections.cisco.cdo.plugins.module_utils.device_inventory.ftd import FTDInventory
from ansible_collections.cisco.cdo.plugins.module_utils.device_inventory.asa import ASA_IOS_Inventory
from ansible_collections.cisco.cdo.plugins.module_utils.device_inventory.delete import DeleteInventory
from ansible_collections.cisco.cdo.plugins.module_utils.device_inventory.inventory import Inventory
from ansible_collections.cisco.cdo.plugins.module_utils.cdo_models import ASA_IOS, FTD, FMC
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


def normalize_device_output(results: list):
    """From the json data returned from the CDO API, use the models defined in
    module_utils/cdo_models.py to determine what data we return to the calling playbook"""
    results = [results] if isinstance(results, dict) else results  # we expect a list
    normalized_devices = list()
    if results:
        for device in results:
            if device.get("deviceType") == "ASA" or device.get("deviceType") == "IOS":
                normalized_devices.append(ASA_IOS.from_json(json.dumps(device)).to_dict())
            elif device.get("deviceType") == "FTDC":
                normalized_devices.append(FTD.from_json(json.dumps(device)).to_dict())
            elif device.get("deviceType") == "FMCE":
                normalized_devices.append(FMC.from_json(json.dumps(device)).to_dict())
    return normalized_devices


def main():
    result = dict(
        msg="", stdout="", stdout_lines=[], stderr="", stderr_lines=[], cdo=None, rc=0, failed=False, changed=False
    )
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
            result["cdo"] = normalize_device_output(inventory_client.gather_inventory())
            result["changed"] = False
        except (CredentialsFailure, APIError) as e:
            result["stderr"] = f"ERROR: {e.message}"
    # Add devices to CDO inventory and return a json dictionary of the new device attributes
    if module.params.get("add"):
        if module.params.get("add", {}).get("ftd"):
            ftd_client = FTDInventory(module.params.get("add", {}).get("ftd"), http_session, endpoint)
            try:
                add_result = ftd_client.add_ftd()
                result["cdo"] = normalize_device_output(add_result)
                result["changed"] = True
            except DuplicateObject as e:
                result["cdo"] = f"Device Not added: {e.message}"
                result["changed"] = False
                result["failed"] = False
            except (AddDeviceFailure, DeviceNotFound, ObjectNotFound, CredentialsFailure) as e:
                result["stderr"] = f"ERROR: {e.message}"
                result["changed"] = False
                result["failed"] = True
        if module.params.get("add", {}).get("asa_ios"):
            try:
                asa_ios_client = ASA_IOS_Inventory(module.params.get("add", {}).get("asa_ios"), http_session, endpoint)
                result["cdo"] = normalize_device_output(asa_ios_client.add_asa_ios())
                result["changed"] = True
            except DuplicateObject as e:
                result["cdo"] = f"Device Not added: {e.message}"
                result["changed"] = False
                result["failed"] = False
            except (SDCNotFound, InvalidCertificate, DeviceUnreachable, CredentialsFailure, APIError) as e:
                result["stderr"] = f"ERROR: {e.message}"
                result["changed"] = False
                result["failed"] = True
    if module.params.get("delete"):# Delete an ASA, FTD, or IOS device from CDO/cdFMC
        try:
            delete_client = DeleteInventory(module.params.get("delete"), http_session, endpoint)
            delete_client.delete_device()
            result["changed"] = True
        except DeviceNotFound as e:
            result["cdo"] = f"Device Not deleted: {e.message}"
            result["changed"] = False
            result["failed"] = False
        except (TooManyMatches) as e:
            result["stderr"] = f"ERROR: {e.message}"

    module.exit_json(**result)


if __name__ == "__main__":
    main()
