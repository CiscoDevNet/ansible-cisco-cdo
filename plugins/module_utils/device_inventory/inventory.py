# -*- coding: utf-8 -*-
#
# Apache License v2.0+ (see LICENSE or https://www.apache.org/licenses/LICENSE-2.0)

from __future__ import absolute_import, division, print_function

__metaclass__ = type

from ansible_collections.cisco.cdo.plugins.module_utils.api_endpoints import CDOAPI
from ansible_collections.cisco.cdo.plugins.module_utils.query import CDOQuery
from ansible_collections.cisco.cdo.plugins.module_utils.api_requests import CDORequests
from ansible_collections.cisco.cdo.plugins.module_utils.errors import DeviceNotFound, ObjectNotFound
import urllib.parse
import requests
import uuid


class Inventory:
    def __init__(self, module_params: dict, http_session: requests.session, endpoint: str):
        self.module_params = module_params
        self.http_session = http_session
        self.endpoint = endpoint
        self.changed = False

    def is_device_in_sync(self, device_info: dict) -> bool:
        "Check to see if the device is out of sync or if there was an OOB Change"
        if device_info.get("configState") != "SYNCED" or device_info.get("oobDetectionState") == "OOB_CHANGE_DETECTED":
            return False
        return True

    def generate_uuid(self):
        # move to utility
        raw_uuid = uuid.uuid4().hex
        return f"{raw_uuid[0:8]}-{raw_uuid[8:12]}-{raw_uuid[12:16]}-{raw_uuid[16:20]}-{raw_uuid[20:]}"

    def get_lar_list(self):
        """Return a list of lars (SDC/CDG from CDO)"""
        path = CDOAPI.LARS.value
        query = CDOQuery.get_lar_query(self.module_params)
        if query is not None:
            path = f"{path}?q={urllib.parse.quote_plus(query)}"
        return CDORequests.get(self.http_session, f"https://{self.endpoint}", path=path)

    def inventory_count(self, filter: str = None):
        """Given a filter criteria, return the number of devices that match the criteria"""
        return CDORequests.get(
            self.http_session, f"https://{self.endpoint}", path=f"{CDOAPI.DEVICES.value}?agg=count&q={filter}"
        )["aggregationQueryResult"]

    def get_specific_device(self, uid: str) -> str:
        """Given a device uid, retrieve the device specific details"""
        path = CDOAPI.SPECIFIC_DEVICE.value.replace("{uid}", uid)
        return CDORequests.get(self.http_session, f"https://{self.endpoint}", path=path)

    def get_device(self, uid: str):
        """Given a device uid, retrieve the specific device model of the device"""
        return CDORequests.get(self.http_session, f"https://{self.endpoint}", path=f"{CDOAPI.DEVICES.value}/{uid}")

    def get_cdfmc(self):
        """Get the cdFMC object for this tenant if one exists"""
        query = CDOQuery.get_cdfmc_query()
        response = CDORequests.get(
            self.http_session, f"https://{self.endpoint}", path=f"{CDOAPI.DEVICES.value}?q={query['q']}"
        )
        if len(response) == 0:
            raise DeviceNotFound("A cdFMC was not found in this tenant")
        return response[0]

    def working_set(self, uid: str):
        """Return a working set object"""
        data = {
            "selectedModelObjects": [{"modelClassKey": "targets/devices", "uuids": [uid]}],
            "workingSetFilterAttributes": [],
        }
        return CDORequests.post(
            self.http_session, f"https://{self.endpoint}", path=f"{CDOAPI.WORKSET.value}", data=data
        )

    def gather_inventory(self, limit: int = 50, offset: int = 0) -> str:
        """Get CDO inventory"""
        # TODO: Support paging
        # TODO: Move the urllib parse to the query lib
        query = CDOQuery.get_inventory_query(self.module_params)
        q = urllib.parse.quote_plus(query["q"])
        r = urllib.parse.quote_plus(query["r"])
        path = f"{CDOAPI.DEVICES.value}?limit={limit}&offset={offset}&q={q}&resolve={r}"
        return CDORequests.get(self.http_session, f"https://{self.endpoint}", path=path)

    def get_cdfmc_access_policy_list(
        self,
        cdfmc_host: str,
        domain_uid: str,
        limit: int = 50,
        offset: int = 0,
        access_list_name=None,
    ):
        # TODO: move to ftd library
        """Given the domain uuid of the cdFMC, retrieve the list of access policies"""
        # TODO: use the FMC collection to retrieve this
        self.http_session.headers["fmc-hostname"] = cdfmc_host
        path = f"{CDOAPI.FMC_ACCESS_POLICY.value.replace('{domain_uid}', domain_uid)}"
        path = f"{path}?{CDOQuery.get_cdfmc_policy_query(limit, offset, access_list_name)}"
        response = CDORequests.get(self.http_session, f"https://{self.endpoint}", path=path)
        if response["paging"]["count"] == 0:
            if access_list_name is not None:
                raise ObjectNotFound(f"Access Policy {access_list_name} not found on cdFMC.")
        return response
