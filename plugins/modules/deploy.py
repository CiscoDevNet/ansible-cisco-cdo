# -*- coding: utf-8 -*-
#
# Apache License v2.0+ (see LICENSE or https://www.apache.org/licenses/LICENSE-2.0)


from __future__ import absolute_import, division, print_function

__metaclass__ = type


DOCUMENTATION = r"""
---
module: deploy

short_description: Check for changes and deploy to devices (FTD, ASA, IOS devices) on Cisco Defense Orchestrator (CDO).

version_added: "1.0.3"

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
    deploy:
        device_type:
            type: str
            required: False
            choices: [asa, ios, ftd, all]
            default: "all"
    pending:
        device_type:
            type: str
            required: False
            choices: [asa, ios, ftd, all]
            default: "all"

author:
    - Aaron Hackney (@aaronhackney)
"""

EXAMPLES = r""" """

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
