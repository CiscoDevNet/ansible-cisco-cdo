# -*- coding: utf-8 -*-
#
# Apache License v2.0+ (see LICENSE or https://www.apache.org/licenses/LICENSE-2.0)


from __future__ import absolute_import, division, print_function

__metaclass__ = type


DOCUMENTATION = r"""
---
module: cmd

short_description: Run arbitrary commands on an ASA or IOS device on Cisco Defense Orchestrator (CDO).

description: This module is to read inventory (FTD, ASA, IOS devices) on Cisco Defense Orchestrator (CDO).

author: Aaron Hackney (@aaronhackney)
"""

# fmt: off
from ansible_collections.cisco.cdo.plugins.module_utils.api_requests import CDORegions, CDORequests
from ansible_collections.cisco.cdo.plugins.module_utils.cmd.cli import CLI
from ansible_collections.cisco.cdo.plugins.module_utils.cmd.template import ApplyTemplate
from ansible_collections.cisco.cdo.plugins.module_utils._version import __version__
from ansible_collections.cisco.cdo.plugins.module_utils.args_common import (
    CMD_ARGUMENT_SPEC,
    CMD_MUTUALLY_REQUIRED_ONE_OF,
    CMD_MUTUALLY_EXCLUSIVE,
    CMD_REQUIRED_IF
)
from ansible_collections.cisco.cdo.plugins.module_utils.errors import RetriesExceeded, CmdExecutionError
from ansible_collections.cisco.cdo.plugins.module_utils.errors import (
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
logger = logging.getLogger('cmd')
fh = logging.FileHandler('/tmp/cmd.log')
fh.setLevel(logging.DEBUG)
logger.setLevel(logging.DEBUG)
logger.addHandler(fh)
logger.debug("Logger started cmd.py......")
# fmt: on


def main():
    result = dict(msg="", stdout="", stdout_lines=[], stderr="", stderr_lines=[], rc=0, failed=False, changed=False)
    module = AnsibleModule(
        argument_spec=CMD_ARGUMENT_SPEC,
        required_one_of=[CMD_MUTUALLY_REQUIRED_ONE_OF],
        mutually_exclusive=CMD_MUTUALLY_EXCLUSIVE,
        required_if=CMD_REQUIRED_IF,
    )
    endpoint = CDORegions[module.params.get("region")].value
    http_session = CDORequests.create_session(module.params.get("api_key"), __version__)

    try:
        if module.params.get("exec_command"):
            cli_client = CLI(module.params.get("exec_command"), http_session, endpoint)
            result["stdout"] = cli_client.run_cmd()
            result["changed"] = True  # TODO: We need to make sure this is true...
        elif module.params.get("apply_template"):
            template_client = ApplyTemplate(module.params.get("apply_template"), http_session, endpoint)
            template_client.apply_config()
            result["stdout"] = template_client.results
            result["changed"] = True  # TODO: We need to make sure this is true...
    except (
        DeviceNotFound,
        TooManyMatches,
        APIError,
        CredentialsFailure,
        RetriesExceeded,
        CmdExecutionError,
        DeviceNotInSync,
    ) as e:
        result["stderr"] = f"ERROR: {e.message}"
    module.exit_json(**result)


if __name__ == "__main__":
    main()
