#!/usr/bin/python
# -*- coding: utf-8 -*-
#
# Apache License v2.0+ (see LICENSE or https://www.apache.org/licenses/LICENSE-2.0)


from __future__ import (absolute_import, division, print_function)
__metaclass__ = type


DOCUMENTATION = r'''
---
module: add_ftd

short_description: This module is to add inventory (FTD devices) on Cisco Defense Orchestrator (CDO).

version_added: "1.0.0"

description: This module is to add inventory (FTD devices) on Cisco Defense Orchestrator (CDO).
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
    add_ftd:
        description: This is the message to send to the test module.
        required: false
        type: dict

author:
    - Aaron Hackney (@aaronhackney)
requirements:
  - pycryptodome
  - requests
  
'''

EXAMPLES = r'''
- name: Add FTD CDO inventory (CLI Method)
  hosts: localhost
  tasks:
    - name: Add FTD to CDO and cdFMC
      cisco.cdo.cdo_add_ftd:
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
      
- name: Add FTD CDO inventory (LTP Method)
  hosts: localhost
  tasks:
    - name: Add FTD to CDO and cdFMC
      cisco.cdo.cdo_add_ftd:
        api_key: "{{ lookup('ansible.builtin.env', 'CDO_API_KEY') }}"
        region: 'us'
        add_ftd:
          onboard_method: 'ltp'
          serial: 'JAD245008W2'
          access_control_policy: 'Default Access Control Policy'
          name: 'ElPaso'
          license:
            - BASE
            - THREAT
            - URLFilter
            - MALWARE
            - PLUS
      register: added_device
'''

# fmt: off 
import requests
import base64
from time import sleep
from ansible_collections.cisco.cdo.plugins.module_utils.api_endpoints import CDOAPI
from ansible_collections.cisco.cdo.plugins.module_utils.requests import CDORegions, CDORequests
from ansible_collections.cisco.cdo.plugins.module_utils.devices import FTDModel, FTDMetaData
from ansible_collections.cisco.cdo.plugins.module_utils.common import inventory_count, get_device, get_cdfmc
from ansible_collections.cisco.cdo.plugins.module_utils.common import get_cdfmc_access_policy_list, get_specific_device
from ansible.module_utils.basic import AnsibleModule
from ansible_collections.cisco.cdo.plugins.module_utils.errors import DeviceNotFound, AddDeviceFailure, DuplicateObject, ObjectNotFound
from ansible_collections.cisco.cdo.plugins.module_utils._version import __version__
from ansible_collections.cisco.cdo.plugins.module_utils.args_common import (
    ADD_FTD_SPEC,
    REQUIRED_ONE_OF,
    MUTUALLY_EXCLUSIVE,
    REQUIRED_IF
)

# fmt: on


def new_ftd_polling(module_params: dict, http_session: requests.session, endpoint: str, uid: str):
    """ Check that the new FTD specific device has been created before attempting move to the onboarding step """
    for i in range(module_params['retry']):
        try:
            return get_specific_device(http_session, endpoint, uid)
        except DeviceNotFound:
            sleep(module_params['delay'])
            continue
    raise AddDeviceFailure(f"Failed to add FTD {module_params['name']}")


def update_ftd_device(http_session: requests.session, endpoint: str, uid: str, data: dict):
    """ Update an FTD object """
    return CDORequests.put(http_session, f"https://{endpoint}", path=f"{CDOAPI.FTDS.value}/{uid}", data=data)


def add_ftd_ltp(module_params: dict, http_session: requests.session, endpoint: str, ftd_device: FTDModel, fmc_uid: str):
    """ Onboard an FTD to cdFMC using LTP (serial number onboarding)"""
    if (not inventory_count(http_session, endpoint, filter=f"serial:{module_params['serial']}") and
            not inventory_count(http_session, endpoint, filter=f"name:{module_params['serial']}")):
        ftd_device.larType = "CDG"
        ftd_device.name = module_params['serial']
        ftd_device.serial = module_params['serial']
        ftd_device.sseDeviceSerialNumberRegistration = dict(
            initialProvisionData=(
                base64.b64encode(f'{{"nkey": "{module_params["password"]}"}}'.encode('ascii')).decode('ascii')
            ),
            sudiSerialNumber=module_params['serial']
        )
        ftd_device.sseEnabled = True

        new_ftd_device = CDORequests.post(http_session, f"https://{endpoint}",
                                          path=CDOAPI.DEVICES.value, data=ftd_device.asdict())
        ftd_specific_device = get_specific_device(http_session, endpoint, new_ftd_device['uid'])  # required polling?
        new_ftd_device = get_device(http_session, endpoint, new_ftd_device['uid'])  # refresh device
        CDORequests.put(http_session, f"https://{endpoint}",
                        path=f"{CDOAPI.FTDS.value}/{ftd_specific_device['uid']}",
                        data={"queueTriggerState": "SSE_CLAIM_DEVICE"}
                        )  # Trigger device claiming
        return ftd_device

    else:
        raise DuplicateObject(f"Device with serial number {module_params['serial']} exists in tenant")


def add_ftd(module_params: dict, http_session: requests.session, endpoint: str):
    """ Add an FTD to CDO via CLI or LTP process """

    try:
        cdfmc = get_cdfmc(http_session, endpoint)
        cdfmc_specific_device = get_specific_device(http_session, endpoint, cdfmc['uid'])
        access_policy = get_cdfmc_access_policy_list(
            http_session, endpoint, cdfmc['host'], cdfmc_specific_device['domainUid'],
            access_list_name=module_params['access_control_policy'])
    except DeviceNotFound as e:
        raise e
    except ObjectNotFound as e:
        raise e

    # TODO: Get these from the fmc collection when it supports cdFMC

    ftd_device = FTDModel(
        name=module_params['name'],
        associatedDeviceUid=cdfmc['uid'],
        metadata=FTDMetaData(
            accessPolicyName=access_policy['items'][0]['name'],
            accessPolicyUuid=access_policy['items'][0]['id'],
            license_caps=','.join(module_params['license']),
            performanceTier=module_params['performance_tier']
        )
    )
    if module_params['onboard_method'].lower() == "ltp":
        ftd_device = add_ftd_ltp(module_params, http_session, endpoint, ftd_device, cdfmc['uid'])
        return f"Serial number {module_params['serial']} ready for LTP onboarding into CDO"
    else:
        new_device = CDORequests.post(http_session, f"https://{endpoint}",
                                      path=CDOAPI.DEVICES.value, data=ftd_device.asdict())
        result = new_ftd_polling(module_params, http_session, endpoint, new_device['uid'])
        update_ftd_device(http_session, endpoint, result['uid'], {"queueTriggerState": "INITIATE_FTDC_ONBOARDING"})
        result = CDORequests.get(http_session, f"https://{endpoint}",
                                 path=f"{CDOAPI.DEVICES.value}/{new_device['uid']}")
        return f"{module_params['name']} CLI Command: {result['metadata']['generatedCommand']}"


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

    module = AnsibleModule(argument_spec=ADD_FTD_SPEC, required_one_of=[
                           REQUIRED_ONE_OF], mutually_exclusive=MUTUALLY_EXCLUSIVE, required_if=REQUIRED_IF)

    endpoint = CDORegions.get_endpoint(module.params.get('region'))
    http_session = CDORequests.create_session(module.params.get('api_key'), __version__)
    try:
        result['stdout'] = add_ftd(module.params.get('add_ftd'), http_session, endpoint)
        result['changed'] = True
    except AddDeviceFailure as e:
        result['stderr'] = f"ERROR: {e.message}"
    except DuplicateObject as e:
        result['stderr'] = f"ERROR: {e.message}"
    except DeviceNotFound as e:
        result['stderr'] = f"ERROR: {e.message}"
    except ObjectNotFound as e:
        result['stderr'] = f"ERROR: {e.message}"
    module.exit_json(**result)


if __name__ == '__main__':
    main()
