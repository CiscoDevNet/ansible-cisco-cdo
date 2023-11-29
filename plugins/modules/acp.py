# -*- coding: utf-8 -*-
#
# Apache License v2.0+ (see LICENSE or https://www.apache.org/licenses/LICENSE-2.0)


from __future__ import absolute_import, division, print_function

__metaclass__ = type


DOCUMENTATION = r"""
---
module: acp

short_description: CRUD Operations for ASA acls in Cisco Defense Orchestrator (CDO).

description: This module is to perform CRUD operations on ASA ACLs in Cisco Defense Orchestrator (CDO).

author: Aaron Hackney (@aaronhackney)
"""

# fmt: off
from ansible_collections.cisco.cdo.plugins.module_utils.api_requests import CDORegions, CDORequests
from ansible_collections.cisco.cdo.plugins.module_utils.acp.acp import AccessPolicies
from ansible_collections.cisco.cdo.plugins.module_utils.device_inventory.inventory import Inventory
from ansible_collections.cisco.cdo.plugins.module_utils._version import __version__
from ansible_collections.cisco.cdo.plugins.module_utils.args_common import (
    ACP_ARGUMENT_SPEC,
    ACP_MUTUALLY_REQUIRED_ONE_OF,
    ACP_MUTUALLY_EXCLUSIVE,
    ACP_REQUIRED_IF
)
from ansible_collections.cisco.cdo.plugins.module_utils.errors import (
    CmdExecutionError,
    RetriesExceeded,
    DeviceNotFound,
    TooManyMatches,
    APIError,
    CredentialsFailure,
    DeviceNotInSync
)
from ansible.module_utils.basic import AnsibleModule
# fmt: on

# fmt: off
# Remove for publishing....
import logging
logging.basicConfig()
logger = logging.getLogger('acp_module')
fh = logging.FileHandler('/tmp/acp_module.log')
fh.setLevel(logging.DEBUG)
logger.setLevel(logging.DEBUG)
logger.addHandler(fh)
logger.debug("acp_module.log logger started......")
# fmt: on


def get_device_uid(module_params, http_session, endpoint):
    inv_client = Inventory(module_params, http_session, endpoint)
    devices = inv_client.gather_inventory()
    for device in devices:
        if device.get("name") == module_params.get("name"):
            return device.get("uid")
    raise DeviceNotFound(f'The specified device {device.get("name")} was not found in CDO inventory')


def main():
    result = dict(msg="", stdout="", stdout_lines=[], stderr="", stderr_lines=[], rc=0, failed=False, changed=False)
    module = AnsibleModule(
        argument_spec=ACP_ARGUMENT_SPEC,
        required_one_of=[ACP_MUTUALLY_REQUIRED_ONE_OF],
        mutually_exclusive=ACP_MUTUALLY_EXCLUSIVE,
        required_if=ACP_REQUIRED_IF,
    )
    endpoint = CDORegions[module.params.get("region")].value
    http_session = CDORequests.create_session(module.params.get("api_key"), __version__)
    logger.debug(f"module parameters {module.params}")
    try:
        if module.params.get("gather"):
            logger.debug("Entering ACP gather...")
            device_uid = get_device_uid(module.params.get("gather"), http_session, endpoint)
            acp_client = AccessPolicies(module.params.get("gather"), http_session, endpoint)
            logger.debug(f"Device UID: {device_uid}")
            logger.debug(f'ACL name: {module.params.get("gather").get("acp_name")}')
            result["cdo"] = acp_client.get_access_control_policies(
                device_uid, acl_name=module.params.get("gather").get("acp_name")
            )
            result["changed"] = False
    except (
        DeviceNotFound,
        TooManyMatches,
        APIError,
        CredentialsFailure,
        RetriesExceeded,
        CmdExecutionError,
        DeviceNotInSync,
    ) as e:
        result["cdo"] = f"{e.message}"
    module.exit_json(**result)


if __name__ == "__main__":
    main()
