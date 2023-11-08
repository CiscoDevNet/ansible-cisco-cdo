# -*- coding: utf-8 -*-
#
# Apache License v2.0+ (see LICENSE or https://www.apache.org/licenses/LICENSE-2.0)


from __future__ import absolute_import, division, print_function

__metaclass__ = type


DOCUMENTATION = r"""
module: deploy
short_description: >-
  Check for changes and deploy to devices (FTD, ASA, IOS devices) on Cisco
  Defense Orchestrator (CDO).
description: >-
  This module is to report pending changes yet to be deployed (FTD, ASA, IOS
  devices) and to actually deploy pending changes to devices through Cisco
  Defense Orchestrator (CDO).
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
  deploy:
    description: Deploy pending configs (Changes staged in CDO) to running devices
    type: dict
    suboptions:
      device_type:
        description: 'The type of devices to deploy (asa, ios, ftd)'
        type: str
        required: false
        choices:
          - asa
          - ios
          - ftd
          - all
        default: all
      device_name:
        description: The CDO inventory name of the device in which we wish to deploy
        type: str
        required: true
      timeout:
        description: >-
          When polling for the deploy to complete, poll this many times.
          The total time before we assume something has gone wrong will be
          the timeout x interval (below)
        type: int
        default: 10
      interval:
        description: The amount of time to wait before checking to see if
        type: int
        default: 1
  pending:
    description: >-
      Just return the pending configs (Changes staged in CDO) but DO NOT DEPLOY
      to any devices
    type: dict
    suboptions:
      device_type:
        description: >-
          The type of devices for which to get the pending configs (asa, ios,
          ftd)
        type: str
        required: false
        choices:
          - asa
          - ios
          - ftd
          - all
        default: all
      device_name:
        description: The CDO inventory name of the device in which we wish to deploy
        type: str
        required: true
      limit:
        description: The number of devices for which to retrieve changes in 1 API call
        type: int
        default: 50
      offset:
        description: Used for paging when records exceed the limit above
        type: int
        default: 0
author:
  - Aaron Hackney (@aaronhackney)

"""

EXAMPLES = r"""
---
- name: Deploy pending device changes
  hosts: all
  connection: local
  tasks:
    - name: Get the pending deploy for all devices in the inventory
      cisco.cdo.deploy:
        api_key: "{{ lookup('ansible.builtin.env', 'CDO_API_KEY') }}"
        region: "{{ lookup('ansible.builtin.env', 'CDO_REGION') }}"
        pending:
          device_type: "{{ hostvars[inventory_hostname].device_type }}"
          device_name: "{{ inventory_hostname }}"
    - name: Deploy pending device changes
      cisco.cdo.deploy:
        api_key: "{{ lookup('ansible.builtin.env', 'CDO_API_KEY') }}"
        region: "{{ lookup('ansible.builtin.env', 'CDO_REGION') }}"
        deploy:
          device_name: "{{ inventory_hostname }}"
          timeout: 20
          interval: 2
"""

# fmt: off
from ansible_collections.cisco.cdo.plugins.module_utils.deploy.deploy import Deploy
from ansible_collections.cisco.cdo.plugins.module_utils.api_requests import CDORegions, CDORequests
from ansible_collections.cisco.cdo.plugins.module_utils._version import __version__
from ansible_collections.cisco.cdo.plugins.module_utils.args_common import (
    DEPLOY_ARGUMENT_SPEC,
    DEPLOY_MUTUALLY_REQUIRED_ONE_OF,
    DEPLOY_MUTUALLY_EXCLUSIVE,
    DEPLOY_REQUIRED_IF
)
from ansible_collections.cisco.cdo.plugins.module_utils.errors import DeviceNotFound, TooManyMatches, APIError, CredentialsFailure
from ansible.module_utils.basic import AnsibleModule
# fmt: on

# TODO: Document and Link with cdFMC Ansible module to deploy staged FTD configs


def main():
    result = dict(msg="", stdout="", stdout_lines=[], stderr="", stderr_lines=[], rc=0, failed=False, changed=False)
    module = AnsibleModule(
        argument_spec=DEPLOY_ARGUMENT_SPEC,
        required_one_of=[DEPLOY_MUTUALLY_REQUIRED_ONE_OF],
        mutually_exclusive=DEPLOY_MUTUALLY_EXCLUSIVE,
        required_if=DEPLOY_REQUIRED_IF,
    )
    endpoint = CDORegions[module.params.get("region")].value
    http_session = CDORequests.create_session(module.params.get("api_key"), __version__)

    # Deploy pending configuration changes to specific device
    if module.params.get("deploy"):
        try:
            deploy_client = Deploy(module.params.get("deploy"), http_session, endpoint)
            result["stdout"] = deploy_client.deploy_changes()
            if result["stdout"]:
                result["changed"] = True
        except (DeviceNotFound, TooManyMatches, APIError, CredentialsFailure) as e:
            result["stderr"] = f"ERROR: {e.message}"

    # Get pending changes for devices
    if module.params.get("pending"):
        try:
            deploy_client = Deploy(module.params.get("pending"), http_session, endpoint)
            result["stdout"] = deploy_client.get_pending_deploy()
        except (DeviceNotFound, APIError, CredentialsFailure) as e:
            result["stderr"] = f"ERROR: {e.message}"

    module.exit_json(**result)


if __name__ == "__main__":
    main()
