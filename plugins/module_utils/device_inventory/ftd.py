# -*- coding: utf-8 -*-
#
# Apache License v2.0+ (see LICENSE or https://www.apache.org/licenses/LICENSE-2.0)

from __future__ import absolute_import, division, print_function

__metaclass__ = type

# fmt: off
import requests
import base64
from time import sleep
from ansible_collections.cisco.cdo.plugins.module_utils.api_endpoints import CDOAPI
from ansible_collections.cisco.cdo.plugins.module_utils.api_requests import CDORequests
from ansible_collections.cisco.cdo.plugins.module_utils.device_inventory.inventory import Inventory
from ansible_collections.cisco.cdo.plugins.module_utils.errors import DeviceNotFound, AddDeviceFailure, DuplicateObject, ObjectNotFound
# fmt: on


class FTD_Inventory:
    def __init__(self, module_params: dict, http_session: requests.session, endpoint: str):
        self.module_params = module_params
        self.http_session = http_session
        self.endpoint = endpoint
        self.changed = False
        self.inventory_client = Inventory(module_params, http_session, endpoint)
        # TODO: Inherit this class from the inventory class

    def new_ftd_polling(self, uid: str):
        """Check that the new FTD specific device has been created before attempting move to the onboarding step"""
        for i in range(self.module_params.get("retry")):
            try:
                return self.inventory_client.get_specific_device(uid)
            except DeviceNotFound:
                sleep(self.module_params.get("delay"))
                continue
        raise AddDeviceFailure(f"Failed to add FTD {self.module_params.get('device_name')}")

    def update_ftd_device(self, uid: str, data: dict):
        """Update an FTD object"""
        return CDORequests.put(
            self.http_session, f"https://{self.endpoint}", path=f"{CDOAPI.FTDS.value}/{uid}", data=data
        )

    def add_ftd_ltp(self, ftd_device: dict, fmc_uid: str):
        """Onboard an FTD to cdFMC using LTP (serial number onboarding)"""

        if not self.inventory_client.inventory_count(
            filter=f"serial:{self.module_params.get('serial')}"
        ) and not self.inventory_client.inventory_count(filter=f"name:{self.module_params.get('serial')}"):
            ftd_device["larType"] = "CDG"
            ftd_device["name"] = self.module_params.get("device_name")
            ftd_device["serial"] = self.module_params.get("serial")
            if self.module_params.get("password"):  # Set the initial admin password
                ftd_device["sseDeviceSerialNumberRegistration"] = dict(
                    initialProvisionData=(
                        base64.b64encode(f'{{"nkey": "{self.module_params.get("password")}"}}'.encode("ascii")).decode(
                            "ascii"
                        )
                    ),
                    sudiSerialNumber=self.module_params.get("serial"),
                )
            else:  # initial password has already been set by the CLI
                ftd_device["sseDeviceSerialNumberRegistration"] = dict(
                    initialProvisionData=base64.b64encode('{"nkey":""}'.encode("ascii")).decode("ascii"),
                    sudiSerialNumber=self.module_params.get("serial"),
                )
            ftd_device["sseEnabled"] = True
            new_ftd_device = CDORequests.post(
                self.http_session, f"https://{self.endpoint}", path=CDOAPI.DEVICES.value, data=ftd_device
            )
            ftd_specific_device = self.inventory_client.get_specific_device(new_ftd_device["uid"])
            new_ftd_device = self.inventory_client.get_device(new_ftd_device["uid"])
            CDORequests.put(
                self.http_session,
                f"https://{self.endpoint}",
                path=f"{CDOAPI.FTDS.value}/{ftd_specific_device['uid']}",
                data={"queueTriggerState": "SSE_CLAIM_DEVICE"},
            )  # Trigger device claiming
            return new_ftd_device

        else:
            raise DuplicateObject(f"Device with serial number {self.module_params.get('serial')} exists in tenant")

    def add_ftd(self):
        """Add an FTD to CDO via CLI or LTP process"""
        try:
            cdfmc = self.inventory_client.get_cdfmc()
            cdfmc_specific_device = self.inventory_client.get_specific_device(cdfmc["uid"])
            access_policy = self.inventory_client.get_cdfmc_access_policy_list(
                cdfmc["host"],
                cdfmc_specific_device["domainUid"],
                access_list_name=self.module_params.get("access_control_policy"),
            )
        except DeviceNotFound as e:
            raise e
        except ObjectNotFound as e:
            raise e

        # TODO: Get these from the fmc collection when it supports cdFMC
        ftd_device = {
            "name": self.module_params.get("device_name"),
            "associatedDeviceUid": cdfmc["uid"],
            "deviceType": "FTDC",
            "model": False,
            "state": "NEW",
            "type": "devices",
            "metadata": {
                "accessPolicyName": access_policy["items"][0]["name"],
                "accessPolicyUuid": access_policy["items"][0]["id"],
                "license_caps": ",".join(self.module_params.get("license")),
                "performanceTier": self.module_params.get("performance_tier"),
            },
        }
        if self.module_params.get("onboard_method").lower() == "ltp":
            return self.add_ftd_ltp(ftd_device, cdfmc["uid"])
        else:
            new_device = CDORequests.post(
                self.http_session, f"https://{self.endpoint}", path=CDOAPI.DEVICES.value, data=ftd_device
            )
            specific_ftd_device = self.new_ftd_polling(new_device["uid"])
            self.update_ftd_device(specific_ftd_device["uid"], {"queueTriggerState": "INITIATE_FTDC_ONBOARDING"})
            return CDORequests.get(
                self.http_session, f"https://{self.endpoint}", path=f"{CDOAPI.DEVICES.value}/{new_device['uid']}"
            )
