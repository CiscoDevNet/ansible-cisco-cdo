# -*- coding: utf-8 -*-
#
# Apache License v2.0+ (see LICENSE or https://www.apache.org/licenses/LICENSE-2.0)


from __future__ import absolute_import, division, print_function

__metaclass__ = type

import requests
from time import sleep
from ansible_collections.cisco.cdo.plugins.module_utils.crypto import CDOCrypto
from ansible_collections.cisco.cdo.plugins.module_utils.api_endpoints import CDOAPI
from ansible_collections.cisco.cdo.plugins.module_utils.api_requests import CDORequests
from ansible_collections.cisco.cdo.plugins.module_utils.device_inventory.inventory import Inventory
from ansible_collections.cisco.cdo.plugins.module_utils.errors import (
    SDCNotFound,
    InvalidCertificate,
    DeviceUnreachable,
    DuplicateObject,
    APIError,
    CredentialsFailure,
)


class ASA_IOS_Inventory(Inventory):
    """Class used for CDO ASA Operations (Extends the Inventory base class in inventory.py)"""

    def __init__(self, module_params: dict, http_session: requests.session, endpoint: str):
        self.module_params = module_params
        self.http_session = http_session
        self.endpoint = endpoint
        self.changed = False

    def connectivity_poll(self, uid: str) -> bool:
        """Check device connectivity or fail after retry attempts have expired"""
        for i in range(self.module_params.get("retry")):
            device = self.get_device(uid)
            if device["connectivityState"] == -2:
                if self.module_params.get("ignore_cert"):
                    self.update_device(uid, data={"ignoreCertificate": True})
                    return True
                else:
                    # TODO: Delete the device we just attempted to add....
                    raise InvalidCertificate(f"{device['connectivityError']}")
            if device["connectivityState"] > -1 or device["status"] == "WAITING_FOR_DATA":
                return True
            sleep(self.module_params.get("delay"))
        raise DeviceUnreachable(
            f"Device {self.module_params.get('device_name')} was not reachable at "
            f"{self.module_params.get('ipv4')}:{self.module_params.get('mgmt_port')} by CDO"
        )

    def asa_credentials_polling(self, uid: str) -> dict:
        """Check credentials have been used successfully  or fail after retry attempts have expired"""
        for i in range(self.module_params.get("retry")):
            result = CDORequests.get(
                self.http_session, f"https://{self.endpoint}", path=f"{CDOAPI.ASA_CONFIG.value}/{uid}"
            )
            if result["state"] == "BAD_CREDENTIALS":
                raise CredentialsFailure(
                    f"Credentials provided for device {self.module_params.get('device_name')} were rejected."
                )
            elif result["state"] == "PENDING_GET_CONFIG_DONE" or result["state"] == "DONE" or result["state"] == "IDLE":
                return result
            sleep(self.module_params.get("delay"))
        raise APIError(
            f"Credentials for device {self.module_params.get('device_name')} were sent but we never reached a known good state."
        )

    def ios_credentials_polling(self, uid: str) -> dict:
        """Check to see if the supplied credentials are accepted by the live device"""
        for i in range(self.module_params.get("retry")):
            device = self.get_device(uid)
            if device["connectivityState"] == -5:
                sleep(self.module_params.get("delay"))
            elif device["connectivityError"] is not None:
                raise CredentialsFailure(device.get("connectivityError"))
            elif device["connectivityState"] > 0:
                return device
        raise CredentialsFailure(f"Device remains in connectivity state {device.get('connectivityState')}")

    def update_device(self, uid: str, data: dict):
        """Update an existing device's attributes"""
        return CDORequests.put(
            self.http_session, f"https://{self.endpoint}", path=f"{CDOAPI.DEVICES.value}/{uid}", data=data
        )

    def add_asa_ios(self):
        """Add ASA or IOS device to CDO"""
        lar_list = self.get_lar_list()
        if not lar_list:
            raise (SDCNotFound("Could not find SDC"))
        else:
            lar = lar_list[0]

        larType = "CDG" if lar["cdg"] else "SDC"
        asa_ios_device = {
            "deviceType": self.module_params.get("device_type").upper(),
            "host": "self.module_params.get('ipv4')",
            "ipv4": f"{self.module_params.get('ipv4')}:{self.module_params.get('mgmt_port')}",
            "larType": larType,
            "larUid": lar["uid"],
            "model": False,
            "name": self.module_params.get("device_name"),
            "ignore_cert": False,
        }

        if self.module_params.get("ignore_cert"):
            asa_ios_device["ignore_cert"] = True

        try:
            path = CDOAPI.DEVICES.value
            device = CDORequests.post(self.http_session, f"https://{self.endpoint}", path=path, data=asa_ios_device)
            self.connectivity_poll(device["uid"])
        except DuplicateObject as e:
            raise e

        creds_crypto = CDOCrypto.encrypt_creds(
            self.module_params.get("username"), self.module_params.get("password"), lar
        )

        if self.module_params.get("device_type").upper() == "ASA":
            creds_crypto["state"] = "CERT_VALIDATED"
            specific_device = self.get_specific_device(device["uid"])
            path = f"{CDOAPI.ASA_CONFIG.value}/{specific_device['uid']}"
            CDORequests.put(self.http_session, f"https://{self.endpoint}", path=path, data=creds_crypto)
            self.asa_credentials_polling(specific_device["uid"])
            return self.get_device(device["uid"])
        elif self.module_params.get("device_type").upper() == "IOS":
            creds_crypto["stateMachineContext"] = {"acceptCert": True}
            path = f"{CDOAPI.DEVICES.value}/{device['uid']}"
            CDORequests.put(self.http_session, f"https://{self.endpoint}", path=path, data=creds_crypto)
            return self.ios_credentials_polling(device["uid"])
