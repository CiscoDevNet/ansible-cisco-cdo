#!/usr/bin/python
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
                default: ''
        asa_ios:
            name:
                type: str
                default: ''
            ipv4:
                type: str
                default:''
            port:
                type: int
                default: 443
            sdc:
                type: str
                default: ''
            username:
                type: str
                default: ''
            password:
                type: str
                default: ''
            ignore_cert:
                type: bool
                default: False
            device_type:
                type: str
                choices: [asa ios]
                default: asa
            retry:
                type: int
                default: 10
            delay:
                type: int
                default: 1
        delete:
            name:
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
- name: Gather inventory from CDO
  hosts: localhost
  tasks:
    - name: Get all network objects for this CDO tenant
      cisco.cdo.net_objects:
        api_key: "{{ lookup('ansible.builtin.env', 'CDO_API_KEY') }}"
        region: "us"
        net_objects: {}
      register: net_objs
      failed_when: (net_objs.stderr is defined) and (net_objs.stderr | length > 0)

- name: Add FTD CDO inventory (Serial number onboarding)
  hosts: localhost
  tasks:
    - name: Add FTD to CDO and cdFMC
      cisco.cdo.inventory:
        api_key: "{{ lookup('ansible.builtin.env', 'CDO_API_KEY') }}"
        region: 'us'
        add:
          ftd:
            onboard_method: 'ltp'
            serial: 'JADXXXXXXXX'
            access_control_policy: 'Default Access Control Policy'
            is_virtual: true
            performance_tier: FTDv10
            license:
              - BASE
              - THREAT
              - URLFilter
              - MALWARE
              - PLUS
      register: added_device
      failed_when: (added_device.stderr is defined) and (added_device.stderr | length > 0)

- name: Add ASA (or IOS) to CDO inventory
  hosts: localhost
  tasks:
    - name: Add ASA to CDO
      cisco.cdo.inventory:
        api_key: "{{ lookup('ansible.builtin.env', 'CDO_API_KEY') }}"
        region: 'us'
        add:
          asa_ios:
            sdc: 'CDO_cisco_aahackne-SDC-1'
            name: 'Austin'
            ipv4: '172.30.4.101'
            port: 8443
            device_type: 'asa'
            username: 'myuser'
            password: 'abc123'
            ignore_cert: true
      register: added_device
      failed_when: (added_device.stderr is defined) and (added_device.stderr | length > 0)

- name: Delete a device from CDO inventory
  hosts: localhost
  tasks:
    - name: Delete ASA from CDO inventory
      cisco.cdo.inventory:
        api_key: "{{ lookup('ansible.builtin.env', 'CDO_API_KEY') }}"
        region: 'us'
        delete:
          name: 'ElPaso'
          device_type: 'ftd'
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
        result["stdout"] = delete_device(module.params.get("delete"), http_session, endpoint)
        result["changed"] = True
    module.exit_json(**result)


if __name__ == "__main__":
    main()
