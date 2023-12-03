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
    def __init__(self, device_uid: str, module_params: dict, http_session: requests.session, endpoint: str) -> None:
        self.http_session = http_session
        self.endpoint = endpoint
        self.features = None
        self.inventory_client = Inventory(module_params, self.http_session, self.endpoint)
        self.config_client = Config(module_params, self.http_session, self.endpoint)
        self.staged_config_uid = None
        self.device_uid = device_uid
        self.ruleset_uid = None
        self.acp_name = module_params.get("acp_name")
        self.limit = 50

    # TODO: make this a post_init call?
    def get_staged_config_uid(self):
        self.staged_config_uid = self.config_client.get_config_summaries(self.device_uid)[0].get(
            "stagedConfigurationUid"
        )

    def get_access_policy(self):
        """Get access-control-list in it's entirety by paging through the api calls until all lines are retrieved."""
        self.get_staged_config_uid()
        rulesets = self.get_rulesets()
        self.ruleset_uid = rulesets.pop().get("uid")
        acp_count = self.get_access_policy_count().get("aggregationQueryResult")
        return self.get_pages(acp_count, self.limit, self._get_access_policy)

    def get_rulesets_count(self) -> dict:
        """Get a count of the number of ACLs on a device"""
        self.get_staged_config_uid()
        query = CDOQuery.rulesets(self.staged_config_uid, count=True)
        return CDORequests.get(
            self.http_session, f"https://{self.endpoint}", path=f"{CDOAPI.RULESETS.value}", query=query
        )

    def get_rulesets(self) -> list:
        """Given a device uid and ruleset name, return information about that one ruleset. If no name
        is provided, return information on all rulesets after paging through all of them"""
        if not self.acp_name:
            rulesets_count = self.get_rulesets_count().get("aggregationQueryResult")
        else:
            rulesets_count = 1
        return self.get_pages(rulesets_count, self.limit, self._get_rulesets).pop()

    def _get_rulesets(self, offset=0) -> list:
        """Given a configuration uid, return a list of ACL descriptors and, if they are applied to interfaces,
        the access-group settings. You can also return a list of just 1 ACL based on the ACL name"""
        query = CDOQuery.rulesets(self.staged_config_uid, name=self.acp_name, limit=self.limit, offset=offset)
        rulesets = CDORequests.get(
            self.http_session, f"https://{self.endpoint}", path=f"{CDOAPI.RULESETS.value}", query=query
        )
        if not rulesets and self.acp_name:
            raise ObjectNotFound(f"Access-Policy {self.acp_name} was not found")
        elif not rulesets:
            raise ObjectNotFound(f"No access-lists found on this ASA")
        return rulesets

    def get_access_policy_count(self) -> dict:
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
