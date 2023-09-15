#!/usr/bin/python
# -*- coding: utf-8 -*-
#
# Apache License v2.0+ (see LICENSE or https://www.apache.org/licenses/LICENSE-2.0)


from __future__ import absolute_import, division, print_function

__metaclass__ = type

# fmt: off
# Remove for publishing....
import logging
logger = logging.getLogger('deploy_module')
logging.basicConfig()
fh = logging.FileHandler('/tmp/deploy.log')
fh.setLevel(logging.DEBUG)
logger.setLevel(logging.DEBUG)
logger.addHandler(fh)
# fmt: on

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
import requests
import urllib.parse
from ansible_collections.cisco.cdo.plugins.module_utils.api_endpoints import CDOAPI
from ansible_collections.cisco.cdo.plugins.module_utils.requests import CDORegions, CDORequests
from ansible_collections.cisco.cdo.plugins.module_utils._version import __version__
from ansible_collections.cisco.cdo.plugins.module_utils.args_common import (
    DEPLOY_ARGUMENT_SPEC,
    DEPLOY_MUTUALLY_REQUIRED_ONE_OF,
    DEPLOY_MUTUALLY_EXCLUSIVE,
    DEPLOY_REQUIRED_IF
)
from ansible_collections.cisco.cdo.plugins.module_utils.query import CDOQuery
from ansible.module_utils.basic import AnsibleModule
# fmt: on

# TODO: accept input for specific device deploy
# TODO: accept input for types of devices to deploy
# TODO: Document and Link with cdFMC Ansible module to deploy staged FTD configs


def get_pending_deploy(
    module_params: dict, http_session: requests.session, endpoint: str, limit: int = 50, offset: int = 0
) -> str:
    q = CDOQuery.pending_changes_query(limit=limit, offset=offset)
    result = CDORequests.get(http_session, f"https://{endpoint}", path=f"{CDOAPI.DEPLOY.value}", query=q)
    pending_change = list()
    for item in result:
        staged_config = dict()
        for event in item.get("changeLogInstance").get("events"):
            staged_config["diff"] = event.get("details")
            staged_config["diff"].pop("_class", None)
            staged_config["user"] = event.get("user")
            staged_config["date"] = event.get("eventDate")
            staged_config["action"] = event.get("action")
            staged_config["change_log_entities"] = list()
            for change_log_path in event.get("changeLogPath").get("enteries"):
                staged_config["change_log_entities"].append(change_log_path.get("name"))
            pending_change.append(staged_config)
    return pending_change


def main():
    result = dict(msg="", stdout="", stdout_lines=[], stderr="", stderr_lines=[], rc=0, failed=False, changed=False)
    module = AnsibleModule(
        argument_spec=DEPLOY_ARGUMENT_SPEC,
        required_one_of=[DEPLOY_MUTUALLY_REQUIRED_ONE_OF],
        mutually_exclusive=DEPLOY_MUTUALLY_EXCLUSIVE,
        required_if=DEPLOY_REQUIRED_IF,
    )

    endpoint = CDORegions.get_endpoint(module.params.get("region"))
    http_session = CDORequests.create_session(module.params.get("api_key"), __version__)

    # Deploy pending configuration changes to devices
    if module.params.get("deploy"):
        result["stdout"] = "deploy selected"

    # Get pending changes for devices
    if module.params.get("pending"):
        pending_deploy = get_pending_deploy(module.params.get("pending"), http_session, endpoint)
        result["stdout"] = pending_deploy

    module.exit_json(**result)


if __name__ == "__main__":
    main()
