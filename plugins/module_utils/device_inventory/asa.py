#!/usr/bin/python
# -*- coding: utf-8 -*-
#
# Apache License v2.0+ (see LICENSE or https://www.apache.org/licenses/LICENSE-2.0)

from time import sleep
from ansible_collections.cisco.cdo.plugins.module_utils.crypto import CDOCrypto
from ansible_collections.cisco.cdo.plugins.module_utils.api_endpoints import CDOAPI
from ansible_collections.cisco.cdo.plugins.module_utils.api_requests import CDORequests
from ansible_collections.cisco.cdo.plugins.module_utils.devices import ASAIOSModel
from ansible_collections.cisco.cdo.plugins.module_utils.common import get_lar_list, get_specific_device, get_device
from ansible_collections.cisco.cdo.plugins.module_utils.errors import (
    SDCNotFound,
    InvalidCertificate,
    DeviceUnreachable,
    DuplicateObject,
    APIError,
    CredentialsFailure,
)
import requests


def connectivity_poll(module_params: dict, http_session: requests.session, endpoint: str, uid: str) -> bool:
    """Check device connectivity or fail after retry attempts have expired"""
    for i in range(module_params.get("retry")):
        device = get_device(http_session, endpoint, uid)
        if device["connectivityState"] == -2:
            if module_params.get("ignore_cert"):
                update_device(http_session, endpoint, uid, data={"ignoreCertificate": True})
                return True
            else:
                # TODO: Delete the device we just attempted to add....
                raise InvalidCertificate(f"{device['connectivityError']}")
        if device["connectivityState"] > -1 or device["status"] == "WAITING_FOR_DATA":
            return True
        sleep(module_params.get("delay"))
    raise DeviceUnreachable(
        f"Device {module_params.get('device_name')} was not reachable at "
        f"{module_params.get('ipv4')}:{module_params.get('mgmt_port')} by CDO"
    )


def asa_credentials_polling(module_params: dict, http_session: requests.session, endpoint: str, uid: str) -> dict:
    """Check credentials have been used successfully  or fail after retry attempts have expired"""
    for i in range(module_params.get("retry")):
        result = CDORequests.get(http_session, f"https://{endpoint}", path=f"{CDOAPI.ASA_CONFIG.value}/{uid}")
        if result["state"] == "BAD_CREDENTIALS":
            raise CredentialsFailure(
                f"Credentials provided for device {module_params.get('device_name')} were rejected."
            )
        elif result["state"] == "PENDING_GET_CONFIG_DONE" or result["state"] == "DONE" or result["state"] == "IDLE":
            return result
        sleep(module_params.get("delay"))
    raise APIError(
        f"Credentials for device {module_params.get('device_name')} were sent but we never reached a known good state."
    )


def ios_credentials_polling(module_params: dict, http_session: requests.session, endpoint: str, uid: str) -> dict:
    """Check to see if the supplied credentials are accepted by the live device"""
    for i in range(module_params.get("retry")):
        device = get_device(http_session, endpoint, uid)
        if device["connectivityState"] == -5:
            sleep(module_params.get("delay"))
        elif device["connectivityError"] is not None:
            raise CredentialsFailure(device.get("connectivityError"))
        elif device["connectivityState"] > 0:
            return device
    raise CredentialsFailure(f"Device remains in connectivity state {device.get('connectivityState')}")


def update_device(http_session: requests.session, endpoint: str, uid: str, data: dict):
    """Update an existing device's attributes"""
    return CDORequests.put(http_session, f"https://{endpoint}", path=f"{CDOAPI.DEVICES.value}/{uid}", data=data)


def add_asa_ios(module_params: dict, http_session: requests.session, endpoint: str):
    """Add ASA or IOS device to CDO"""

    lar_list = get_lar_list(module_params, http_session, endpoint)
    if len(lar_list) != 1:
        raise (SDCNotFound("Could not find SDC"))
    else:
        lar = lar_list[0]

    asa_ios_device = ASAIOSModel(
        deviceType=module_params.get("device_type").upper(),
        host=module_params.get("ipv4"),
        ipv4=f"{module_params.get('ipv4')}:{module_params.get('mgmt_port')}",
        larType="CDG" if lar["cdg"] else "SDC",
        larUid=lar["uid"],
        model=False,
        name=module_params.get("device_name"),
    )

    if module_params.get("ignore_cert"):
        asa_ios_device.ignore_cert = False

    try:
        path = CDOAPI.DEVICES.value
        device = CDORequests.post(http_session, f"https://{endpoint}", path=path, data=asa_ios_device.asdict())
        connectivity_poll(module_params, http_session, endpoint, device["uid"])
    except DuplicateObject as e:
        raise e

    creds_crypto = CDOCrypto.encrypt_creds(module_params.get("username"), module_params.get("password"), lar)

    if module_params.get("device_type").upper() == "ASA":
        creds_crypto["state"] = "CERT_VALIDATED"
        specific_device = get_specific_device(http_session, endpoint, device["uid"])
        path = f"{CDOAPI.ASA_CONFIG.value}/{specific_device['uid']}"
        CDORequests.put(http_session, f"https://{endpoint}", path=path, data=creds_crypto)
        asa_credentials_polling(module_params, http_session, endpoint, specific_device["uid"])
        return get_device(http_session, endpoint, device["uid"])
    elif module_params.get("device_type").upper() == "IOS":
        creds_crypto["stateMachineContext"] = {"acceptCert": True}
        path = f"{CDOAPI.DEVICES.value}/{device['uid']}"
        CDORequests.put(http_session, f"https://{endpoint}", path=path, data=creds_crypto)
        return ios_credentials_polling(module_params, http_session, endpoint, device["uid"])
