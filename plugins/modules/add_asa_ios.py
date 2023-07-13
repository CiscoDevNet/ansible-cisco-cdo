#!/usr/bin/python
# -*- coding: utf-8 -*-
#
# Apache License v2.0+ (see LICENSE or https://www.apache.org/licenses/LICENSE-2.0)

from __future__ import (absolute_import, division, print_function)
__metaclass__ = type

DOCUMENTATION = r'''
---
module: add_asa_ios

short_description: This module is to add inventory (ASA, IOS devices) on Cisco Defense Orchestrator (CDO).

version_added: "1.0.0"

description: This module is to add inventory (ASA, IOS devices) on Cisco Defense Orchestrator (CDO). 
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
'''
# fmt: off 
from time import sleep
from ansible_collections.cisco.cdo.plugins.module_utils.crypto import CDOCrypto
from ansible_collections.cisco.cdo.plugins.module_utils.api_endpoints import CDOAPI
from ansible_collections.cisco.cdo.plugins.module_utils.requests import CDORegions, CDORequests
from ansible_collections.cisco.cdo.plugins.module_utils.devices import ASAIOSModel
from ansible_collections.cisco.cdo.plugins.module_utils.common import get_lar_list, get_specific_device, get_device
from ansible_collections.cisco.cdo.plugins.module_utils._version import __version__

from ansible_collections.cisco.cdo.plugins.module_utils.errors import (
    SDCNotFound,
    InvalidCertificate,
    DeviceUnreachable,
    DuplicateObject,
    APIError,
    CredentialsFailure
)
from ansible_collections.cisco.cdo.plugins.module_utils.errors import (
    SDCNotFound,
    InvalidCertificate,
    DeviceUnreachable,
    APIError,
    CredentialsFailure
)

from ansible_collections.cisco.cdo.plugins.module_utils.args_common import (
    ADD_ASA_IOS_SPEC,
    REQUIRED_ONE_OF,
    MUTUALLY_EXCLUSIVE,
    REQUIRED_IF
)

from ansible.module_utils.basic import AnsibleModule
import requests
# fmt: on


def connectivity_poll(module_params: dict, http_session: requests.session, endpoint: str, uid: str) -> bool:
    """ Check device connectivity or fail after retry attempts have expired"""
    for i in range(module_params['retry']):
        device = get_device(http_session, endpoint, uid)
        if device['connectivityState'] == -2:
            if module_params['ignore_cert']:
                update_device(http_session, endpoint, uid, data={"ignoreCertificate": True})
                return True
            else:
                # TODO: Delete the device we just attempted to add....
                raise InvalidCertificate(f"{device['connectivityError']}")
        if device['connectivityState'] > -1 or device['status'] == "WAITING_FOR_DATA":
            return True
        sleep(module_params['delay'])
    raise DeviceUnreachable(
        f"Device {module_params['name']} was not reachable at "
        f"{module_params['ipv4']}:{module_params['port']} by CDO"
    )


def asa_credentails_polling(module_params: dict, http_session: requests.session, endpoint: str, uid: str) -> bool:
    """ Check credentials have been used successfully  or fail after retry attempts have expired"""
    for i in range(module_params['retry']):
        result = CDORequests.get(
            http_session, f"https://{endpoint}", path=f"{CDOAPI.ASA_CONFIG.value}/{uid}")
        if result['state'] == "BAD_CREDENTIALS":
            raise CredentialsFailure(
                f"Credentials provided for device {module_params['name']} were rejected.")
        elif result['state'] == "PENDING_GET_CONFIG_DONE" or result['state'] == "DONE" or result['state'] == "IDLE":
            return True
        sleep(module_params['delay'])
    raise APIError(
        f"Credentials for device {module_params['name']} were sent but we never reached a known good state.")


def ios_credentials_polling(module_params: dict, http_session: requests.session, endpoint: str, uid: str) -> bool:
    """ Check to see if the supplied credentials are accepted by the live device """
    for i in range(module_params['retry']):
        device = get_device(http_session, endpoint, uid)
        if device['connectivityState'] == -5:
            sleep(module_params['delay'])
        elif device['connectivityError'] is not None:
            raise CredentialsFailure(device['connectivityError'])
        elif device['connectivityState'] > 0:
            return True
    raise CredentialsFailure(f"Device remains in connectivity state {device['connectivityState']}")


def update_device(http_session: requests.session, endpoint: str, uid: str, data: dict):
    """ Update an eixsting device's attributes """
    return CDORequests.put(http_session, f"https://{endpoint}", path=f"{CDOAPI.DEVICES.value}/{uid}", data=data)


def add_asa_ios(module_params: dict, http_session: requests.session, endpoint: str):
    """ Add ASA or IOS device to CDO"""

    lar_list = get_lar_list(module_params, http_session, endpoint)
    if len(lar_list) != 1:
        raise (SDCNotFound(f"Could not find SDC"))
    else:
        lar = lar_list[0]

    asa_ios_device = ASAIOSModel(deviceType=module_params['device_type'].upper(),
                                 host=module_params['ipv4'],
                                 ipv4=f"{module_params['ipv4']}:{module_params['port']}",
                                 larType='CDG' if lar['cdg'] else 'SDC',
                                 larUid=lar['uid'],
                                 model=False,
                                 name=module_params['name']
                                 )

    if module_params['ignore_cert']:
        asa_ios_device.ignore_cert = False

    try:
        path = CDOAPI.DEVICES.value
        device = CDORequests.post(http_session, f"https://{endpoint}", path=path, data=asa_ios_device.asdict())
        connectivity_poll(module_params, http_session, endpoint, device['uid'])
    except DuplicateObject as e:
        raise e

    creds_crypto = CDOCrypto.encrypt_creds(module_params['username'], module_params['password'], lar)

    if module_params['device_type'].upper() == "ASA":
        creds_crypto['state'] = "CERT_VALIDATED"
        specific_device = get_specific_device(http_session, endpoint, device['uid'])
        path = f"{CDOAPI.ASA_CONFIG.value}/{specific_device['uid']}"
        CDORequests.put(http_session, f"https://{endpoint}", path=path, data=creds_crypto)
        asa_credentails_polling(module_params, http_session, endpoint, specific_device['uid'])
    elif module_params['device_type'].upper() == "IOS":
        creds_crypto['stateMachineContext'] = {"acceptCert": True}
        path = f"{CDOAPI.DEVICES.value}/{device['uid']}"
        CDORequests.put(http_session, f"https://{endpoint}", path=path, data=creds_crypto)
        ios_credentials_polling(module_params, http_session, endpoint, device['uid'])
    return f"{module_params['device_type'].upper()} {module_params['name']} added to CDO"


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
    module = AnsibleModule(argument_spec=ADD_ASA_IOS_SPEC, required_one_of=[
                           REQUIRED_ONE_OF], mutually_exclusive=MUTUALLY_EXCLUSIVE, required_if=REQUIRED_IF)
    endpoint = CDORegions.get_endpoint(module.params.get('region'))
    http_session = CDORequests.create_session(module.params.get('api_key'), __version__)
    module_params = module.params.get('add_asa_ios')

    try:
        result['stdout'] = add_asa_ios(module_params,  http_session, endpoint)
        result['changed'] = True
    except SDCNotFound as e:
        result['stderr'] = f"ERROR: {e.message}"
    except InvalidCertificate as e:
        result['stderr'] = f"ERROR: {e.message}"
    except DeviceUnreachable as e:
        result['stderr'] = f"ERROR: {e.message}"
    except CredentialsFailure as e:
        result['stderr'] = f"ERROR: {e.message}"
    except DuplicateObject as e:
        result['stderr'] = f"ERROR: {e.message}"
    except APIError as e:
        result['stderr'] = f"ERROR: {e.message}"

    module.exit_json(**result)


if __name__ == '__main__':
    main()
