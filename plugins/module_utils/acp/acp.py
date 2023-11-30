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
        self.ruleset_uid = None
        self.ruleset_length = None
        self.limit = 50

    # TODO: move the checks to the called functions and simplify this....
    def get_access_policy(self, uid: str, acl_name: str = ""):
        config_summary = self.config_client.get_config_summaries(uid)
        if not config_summary:
            raise ObjectNotFound(f"Could not find a config summary for device {self.module_params.get('name')}")
        rulesets = self.get_rulesets(config_summary[0].get("stagedConfigurationUid"), name=acl_name)
        if not rulesets and acl_name:
            raise ObjectNotFound(f"Access-Policy {acl_name} was not found")
        elif not rulesets:
            raise ObjectNotFound(f"No access-lists found on this ASA")
        self.ruleset_uid = rulesets[0].get("uid")
        self.ruleset_length = self.get_access_policy_length().get("aggregationQueryResult")
        return self.get_pages(self.ruleset_length, self.limit, self._get_access_policy)

    def get_rulesets_count(self, configuration_uid: str) -> dict:
        query = CDOQuery.rulesets(configuration_uid, count=True)
        return CDORequests.get(
            self.http_session, f"https://{self.endpoint}", path=f"{CDOAPI.RULESETS.value}", query=query
        )

    # TODO: Set up paging...
    def get_rulesets(self, configuration_uid: str, name="") -> list:
        """Given a configuration uid, return a list of ACL descriptors and, if they are applied to interfaces,
        the access-group settings. You can also return a list of just 1 ACL based on the ACL name"""
        query = CDOQuery.rulesets(configuration_uid, name=name)
        return CDORequests.get(
            self.http_session, f"https://{self.endpoint}", path=f"{CDOAPI.RULESETS.value}", query=query
        )

    def get_access_policy_length(self) -> dict:
        """Given the Access Policy ruleSetUid, return the number of rules in that policy"""
        query = {"q": f"ruleSetUid:{self.ruleset_uid}", "agg": "count"}
        return CDORequests.get(
            self.http_session, f"https://{self.endpoint}", path=f"{CDOAPI.FIREWALL_RULES.value}", query=query
        )

    def _get_access_policy(self, offset=0):
        query = CDOQuery.access_policy(self.ruleset_uid, limit=self.limit, offset=offset)
        return CDORequests.get(
            self.http_session, f"https://{self.endpoint}", path=f"{CDOAPI.FIREWALL_RULES.value}", query=query
        )

    # TODO: Make this a utility function for reuse in other libs
    def get_pages(self, total_records: int, limit: int, api_fn: Callable) -> list:
        """Loop through the pages of data until we have all of the data records."""
        result_list = list()
        iterations = total_records // limit
        if total_records % limit != 0:
            iterations += 1
        offset = 0
        for i in range(iterations):
            result_list.append(api_fn(offset=offset))
            offset += limit
        return result_list
