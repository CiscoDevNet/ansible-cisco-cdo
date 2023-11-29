# -*- coding: utf-8 -*-
#
# Apache License v2.0+ (see LICENSE or https://www.apache.org/licenses/LICENSE-2.0)

from __future__ import absolute_import, division, print_function

__metaclass__ = type

import requests
from typing import Callable
from ansible_collections.cisco.cdo.plugins.module_utils.api_endpoints import CDOAPI
from ansible_collections.cisco.cdo.plugins.module_utils.query import CDOQuery
from ansible_collections.cisco.cdo.plugins.module_utils.api_requests import CDORequests
from ansible_collections.cisco.cdo.plugins.module_utils.device_inventory.inventory import Inventory
from ansible_collections.cisco.cdo.plugins.module_utils.config.config import Config
from ansible_collections.cisco.cdo.plugins.module_utils.errors import DeviceNotFound, ObjectNotFound

# fmt: off
# Remove for publishing....
import logging
logging.basicConfig()
logger = logging.getLogger('acl_helper')
fh = logging.FileHandler('/tmp/acl_helper.log')
fh.setLevel(logging.DEBUG)
logger.setLevel(logging.DEBUG)
logger.addHandler(fh)
logger.debug("acl_helper.log logger started......")
# fmt: on


class AccessPolicies:
    def __init__(self, module_params: dict, http_session: requests.session, endpoint: str) -> None:
        self.module_params = module_params
        self.http_session = http_session
        self.endpoint = endpoint
        self.staged_config_uid = ""
        self.features = None
        self.inventory_client = Inventory(self.module_params, self.http_session, self.endpoint)
        self.config_client = Config(self.module_params, self.http_session, self.endpoint)
        self.device_uid = None

    def get_access_control_policies(self, uid: str, acl_name: str = "") -> list:
        """Return a list of the ASA access control lists. If a name is provided, only return that ACL"""
        config_summary = self.config_client.get_config_summaries(uid)
        if not config_summary:
            raise ObjectNotFound(f"Could not find a config summary for device {self.module_params.get('name')}")
        rulesets = self.get_rulesets(config_summary[0].get("stagedConfigurationUid"), name=acl_name)
        if not rulesets and acl_name:
            raise ObjectNotFound(f"Access-Policy {acl_name} was not found")
        elif not rulesets:
            raise ObjectNotFound(f"No access-lists found on this ASA")
        return self.get_access_policy(rulesets[0].get("uid"))

    def get_rulesets_count(self, configuration_uid: str) -> dict:
        query = CDOQuery.rulesets(configuration_uid, count=True)
        return CDORequests.get(
            self.http_session, f"https://{self.endpoint}", path=f"{CDOAPI.RULESETS.value}", query=query
        )

    # TODO: Paging if rulesets are more than 50
    def get_rulesets(self, configuration_uid: str, name="") -> list:
        """Given a configuration uid, return a list of ACL descriptors and, if they are applied to interfaces,
        the access-group settings. You can also return a list of just 1 ACL based on the ACL name"""
        query = CDOQuery.rulesets(configuration_uid, name=name)
        return CDORequests.get(
            self.http_session, f"https://{self.endpoint}", path=f"{CDOAPI.RULESETS.value}", query=query
        )

    def get_access_policy_length(self, ruleset_uid: str) -> dict:
        """Given the Access Policy ruleSetUid, return the number of rules in that policy"""
        query = {"q": f"ruleSetUid:{ruleset_uid}", "agg": "count"}
        return CDORequests.get(
            self.http_session, f"https://{self.endpoint}", path=f"{CDOAPI.FIREWALL_RULES.value}", query=query
        )

    # TODO: Set up paging...
    def get_access_policy(self, ruleset_uid: str, offset=0, limit=50, count: bool = False):
        query = CDOQuery.access_policy(ruleset_uid, limit=limit, offset=offset)
        return CDORequests.get(
            self.http_session, f"https://{self.endpoint}", path=f"{CDOAPI.FIREWALL_RULES.value}", query=query
        )

    # TODO make this a generic paging for any fn (Using args/kwargs?)
    def get_access_policy_rules(total_records: int, limit: int, api_fn: Callable) -> list:
        # Using the total number of records and the limit, call the fcn to get
        # the results in a loop until we have all of the records and then return
        # them
        result_list = list()
        iterations = total_records // limit
        if total_records % limit != 0:
            iterations += 1
        offset = 0

        if total_records < limit:
            return api_fn()
        else:
            for i in range(iterations):
                result_list.append(api_fn(offset=offset).json())
                offset += limit
        return result_list


# https://www.defenseorchestrator.com/aegis/rest/v1/services/targets/firewallrules?q=ruleSetUid%3A32442140-79f9-406a-9ea7-c47022d47d58&agg=count
