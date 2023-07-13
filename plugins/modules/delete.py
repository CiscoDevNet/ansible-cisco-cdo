#!/usr/bin/python
# -*- coding: utf-8 -*-
#
# Apache License v2.0+ (see LICENSE or https://www.apache.org/licenses/LICENSE-2.0)


from __future__ import (absolute_import, division, print_function)
__metaclass__ = type

DOCUMENTATION = r'''
---
module: delete

short_description: This module is to remove inventory (FTD, ASA, IOS devices) on Cisco Defense Orchestrator (CDO).

version_added: "1.0.0"

description: This module is to remove inventory (FTD, ASA, IOS devices) on Cisco Defense Orchestrator (CDO).
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
    add_ftd:
        description: This is the message to send to the test module.
        required: false
        type: dict
    add_asa:
        description:
            - Control to demo if the result of this module is changed or not.
            - Parameter description can be a list as well.
        required: false
        type: bool

author:
    - Aaron Hackney (@aaronhackney)
requirements:
  - pycryptodome
  - requests
  
'''

EXAMPLES = r'''
- name: Add FTD CDO inventory
  hosts: localhost
  tasks:
    - name: Add FTD to CDO and cdFMC
      cisco.cdo.cdo_inventory:
        api_key: "{{ lookup('ansible.builtin.env', 'CDO_API_KEY') }}"
        region: 'us'
        add_ftd:
          onboard_method: 'cli'
          access_control_policy: 'Default Access Control Policy'
          name: 'ElPaso'
          is_virtual: true
          performance_tier: FTDv10
          license:
            - BASE
            - THREAT
            - URLFilter
            - MALWARE
            - PLUS
      register: added_device

---
- name: Add ASA to CDO inventory
  hosts: localhost
  tasks:
    - name: Add ASA to CDO
      cisco.cdo.cdo_inventory:
        api_key: "{{ lookup('ansible.builtin.env', 'CDO_API_KEY') }}"
        region: 'us'
        add_asa:
          sdc: 'CDO_cisco_aahackne-SDC-1'
          name: 'Austin'
          ipv4: '172.30.4.101'
          port: 8443
          device_type: 'asa'
          username: 'myuser'
          password: 'abc123'
          ignore_cert: true
      register: added_device

---
- name: Add IOS to CDO inventory
  hosts: localhost
  tasks:
    - name: Add IOS to CDO
      cisco.cdo.cdo_inventory:
        api_key: "{{ lookup('ansible.builtin.env', 'CDO_API_KEY') }}"
        region: 'us'
        add_asa_ios:
          sdc: 'CDO_cisco_aahackne-SDC-1'
          name: 'Austin-CSR-1000v'
          ipv4: '172.30.4.250'
          port: 22
          device_type: 'ios'
          username: 'myuser'
          password: 'abc123'
          ignore_cert: true
      register: added_device    
---
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
'''

# fmt: off 
from ansible_collections.cisco.cdo.plugins.module_utils.api_endpoints import CDOAPI
from ansible_collections.cisco.cdo.plugins.module_utils.requests import CDORegions, CDORequests
from ansible_collections.cisco.cdo.plugins.module_utils.common import working_set, get_cdfmc, get_specific_device, inventory
from ansible_collections.cisco.cdo.plugins.module_utils._version import __version__
from ansible_collections.cisco.cdo.plugins.module_utils.args_common import (
    DELETE_SPEC,
    REQUIRED_ONE_OF,
    MUTUALLY_EXCLUSIVE,
    REQUIRED_IF
)
from ansible.module_utils.basic import AnsibleModule
import ansible_collections.cisco.cdo.plugins.module_utils.errors as cdo_errors
import requests
# fmt: on


def find_device_for_deletion(module_params: dict, http_session: requests.session, endpoint: str):
    """ Find the object we intend to delete """
    if module_params['device_type'].upper() == "FTD":
        extra_filter = "AND (deviceType:FTDC)"
    else:
        extra_filter = f"AND (deviceType:{module_params['device_type'].upper()})"
    module_params['filter'] = module_params['name']
    device_list = inventory(module_params, http_session, endpoint, extra_filter=extra_filter)
    if len(device_list) < 1:
        raise cdo_errors.DeviceNotFound(f"Cannot delete {module_params['name']} - device by that name not found")
    elif len(device_list) > 1:
        raise cdo_errors.TooManyMatches(f"Cannot delete {module_params['name']} - more than 1 device matches name")
    else:
        return device_list[0]


def delete_device(module_params: dict, http_session: requests.session, endpoint: str):
    """ Orchestrate deleting the device """
    device = find_device_for_deletion(module_params, http_session, endpoint)
    working_set(http_session, endpoint, device['uid'])
    if module_params['device_type'].upper() == "ASA" or module_params['device_type'].upper() == "IOS":
        CDORequests.delete(http_session, f"https://{endpoint}", path=f"{CDOAPI.DEVICES.value}/{device['uid']}")
    elif module_params['device_type'].upper() == "FTD":
        cdfmc = get_cdfmc(http_session, endpoint)
        cdfmc_specific_device = get_specific_device(http_session, endpoint, cdfmc['uid'])
        data = {
            "queueTriggerState": "PENDING_DELETE_FTDC",
            "stateMachineContext": {"ftdCDeviceIDs": f"{device['uid']}"}
        }
        result = CDORequests.put(http_session, f"https://{endpoint}",
                                 path=f"{CDOAPI.FMC.value}/{cdfmc_specific_device['uid']}", data=data)


def main():
    result = dict(
        msg='',
        stdout='',
        stdout_lines=[],
        stderr='',
        stderr_lines=[],
        rc=0,
        failed=False,
        changed=False
    )

    module = AnsibleModule(argument_spec=DELETE_SPEC, required_one_of=[
                           REQUIRED_ONE_OF], mutually_exclusive=MUTUALLY_EXCLUSIVE, required_if=REQUIRED_IF)

    endpoint = CDORegions.get_endpoint(module.params.get('region'))
    http_session = CDORequests.create_session(module.params.get('api_key'), __version__)
    result['stdout'] = delete_device(module.params.get('delete'), http_session, endpoint)
    result['changed'] = True
    module.exit_json(**result)


if __name__ == '__main__':
    main()
