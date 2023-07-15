#!/usr/bin/python
# -*- coding: utf-8 -*-
#
# Apache License v2.0+ (see LICENSE or https://www.apache.org/licenses/LICENSE-2.0)


from __future__ import absolute_import, division, print_function

__metaclass__ = type

# fmt: off
# Remove for publishing....
import logging
logging.basicConfig()
logger = logging.getLogger('net_obj')
fh = logging.FileHandler('/tmp/cdo.log')
fh.setLevel(logging.DEBUG)
logger.setLevel(logging.DEBUG)
logger.addHandler(fh)
logger.debug("Logger started......")
# fmt: on

DOCUMENTATION = r"""
---
module: net_objects

short_description: This module is to mange network objcets and object-groups on Cisco Defense Orchestrator (CDO).

version_added: "1.1.0"

description: This module is to read inventory (FTD, ASA, IOS devices) on Cisco Defense Orchestrator (CDO).
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
    net_objects:
        description:
            - Operations on network objects
        required: false
        type: dict
author:
    - Aaron Hackney (@aaronhackney)
requirements:
  - requests

"""

EXAMPLES = r"""
- name: Get device inventory details
  hosts: localhost
  tasks:
    - name: Get the CDO inventory for this tenant
      cisco.cdo.cdo_inventory:
        api_key: "{{ lookup('ansible.builtin.env', 'CDO_API_KEY') }}"
        region: "us"

"""

# fmt: off
from ansible_collections.cisco.cdo.plugins.module_utils.requests import CDORegions, CDORequests
from ansible_collections.cisco.cdo.plugins.module_utils.api_endpoints import CDOAPI
from ansible_collections.cisco.cdo.plugins.module_utils.query import CDOQuery
from ansible_collections.cisco.cdo.plugins.module_utils.common import get_net_objs
from ansible_collections.cisco.cdo.plugins.module_utils._version import __version__
from ansible_collections.cisco.cdo.plugins.module_utils.args_common import (
    NET_OBJS_ARGUMENT_SPEC,
    NET_OBJS_REQUIRED,
    NET_OBJS_MUTUALLY_EXCLUSIVE,
    NET_OBJS_REQUIRED_IF
)
from ansible.module_utils.basic import AnsibleModule
# fmt: on


def main():
    result = dict(msg="", stdout="", stdout_lines=[], stderr="", stderr_lines=[], rc=0, failed=False, changed=False)

    module = AnsibleModule(
        argument_spec=NET_OBJS_ARGUMENT_SPEC,
        required_one_of=[NET_OBJS_REQUIRED],
        mutually_exclusive=NET_OBJS_MUTUALLY_EXCLUSIVE,
        required_if=NET_OBJS_REQUIRED_IF,
    )

    endpoint = CDORegions.get_endpoint(module.params.get("region"))
    http_session = CDORequests.create_session(module.params.get("api_key"), __version__)
    result["stdout"] = get_net_objs(module.params.get("net_objects"), http_session, endpoint)

    module.exit_json(**result)


if __name__ == "__main__":
    main()
