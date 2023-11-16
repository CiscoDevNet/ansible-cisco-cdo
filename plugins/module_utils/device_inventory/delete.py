# -*- coding: utf-8 -*-
#
# Apache License v2.0+ (see LICENSE or https://www.apache.org/licenses/LICENSE-2.0)

from __future__ import absolute_import, division, print_function

__metaclass__ = type

# fmt: off
from ansible_collections.cisco.cdo.plugins.module_utils.api_endpoints import CDOAPI
from ansible_collections.cisco.cdo.plugins.module_utils.api_requests import CDORequests
from ansible_collections.cisco.cdo.plugins.module_utils.device_inventory.inventory import Inventory
from ansible_collections.cisco.cdo.plugins.module_utils.errors import DeviceNotFound, TooManyMatches
import requests
# fmt: on

class DeleteInventory(Inventory):
    """Class used to remove ASA/IOS/FTD devices from CDO/cdFMC (Extends the Inventory base class in inventory.py)"""
    def __init__(self, module_params: dict, http_session: requests.session, endpoint: str):
        self.module_params = module_params
        self.http_session = http_session
        self.endpoint = endpoint
        self.changed = False

    def find_device_for_deletion(self):
        """Find the object we intend to delete"""
        # TODO: Paging for large device lists
        self.module_params["filter"] = self.module_params.get("device_name")
        device_list = self.gather_inventory()
        if not device_list:
            raise DeviceNotFound(
                f"Cannot delete {self.module_params.get('device_name')} - device by that name not found"
            )
        elif len(device_list) > 1:
            raise TooManyMatches(
                f"Cannot delete {self.module_params.get('device_name')} - more than 1 device matches name"
            )
        else:
            return device_list[0]

    def delete_device(self):
        """Orchestrate deleting the device"""
        try:
            device = self.find_device_for_deletion()
            self.working_set(device["uid"])
            if (
                self.module_params.get("device_type").upper() == "ASA"
                or self.module_params.get("device_type").upper() == "IOS"
            ):
                response = CDORequests.delete(
                    self.http_session, f"https://{self.endpoint}", path=f"{CDOAPI.DEVICES.value}/{device['uid']}"
                )
                return response

            elif self.module_params.get("device_type").upper() == "FTD":
                cdfmc = self.get_cdfmc()
                cdfmc_specific_device = self.get_specific_device(cdfmc["uid"])
                data = {
                    "queueTriggerState": "PENDING_DELETE_FTDC",
                    "stateMachineContext": {"ftdCDeviceIDs": f"{device['uid']}"},
                }
                response = CDORequests.put(
                    self.http_session,
                    f"https://{self.endpoint}",
                    path=f"{CDOAPI.FMC.value}/{cdfmc_specific_device['uid']}",
                    data=data,
                )
                return response
        except DeviceNotFound as e:
            raise e
