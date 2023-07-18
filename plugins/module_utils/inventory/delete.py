#!/usr/bin/python
# -*- coding: utf-8 -*-
#
# Apache License v2.0+ (see LICENSE or https://www.apache.org/licenses/LICENSE-2.0)

# fmt: off
from ansible_collections.cisco.cdo.plugins.module_utils.api_endpoints import CDOAPI
from ansible_collections.cisco.cdo.plugins.module_utils.requests import CDORequests
from ansible_collections.cisco.cdo.plugins.module_utils.common import working_set, get_cdfmc, get_specific_device, gather_inventory
from ansible_collections.cisco.cdo.plugins.module_utils._version import __version__
import ansible_collections.cisco.cdo.plugins.module_utils.errors as cdo_errors
import requests
# fmt: on


def find_device_for_deletion(module_params: dict, http_session: requests.session, endpoint: str):
    """Find the object we intend to delete"""
    if module_params["device_type"].upper() == "FTD":
        extra_filter = "AND (deviceType:FTDC)"
    else:
        extra_filter = f"AND (deviceType:{module_params['device_type'].upper()})"
    module_params["filter"] = module_params["name"]
    device_list = gather_inventory(module_params, http_session, endpoint, extra_filter=extra_filter)
    if len(device_list) < 1:
        raise cdo_errors.DeviceNotFound(f"Cannot delete {module_params['name']} - device by that name not found")
    elif len(device_list) > 1:
        raise cdo_errors.TooManyMatches(f"Cannot delete {module_params['name']} - more than 1 device matches name")
    else:
        return device_list[0]


def delete_device(module_params: dict, http_session: requests.session, endpoint: str):
    """Orchestrate deleting the device"""
    device = find_device_for_deletion(module_params, http_session, endpoint)
    working_set(http_session, endpoint, device["uid"])
    if module_params["device_type"].upper() == "ASA" or module_params["device_type"].upper() == "IOS":
        CDORequests.delete(http_session, f"https://{endpoint}", path=f"{CDOAPI.DEVICES.value}/{device['uid']}")
    elif module_params["device_type"].upper() == "FTD":
        cdfmc = get_cdfmc(http_session, endpoint)
        cdfmc_specific_device = get_specific_device(http_session, endpoint, cdfmc["uid"])
        data = {
            "queueTriggerState": "PENDING_DELETE_FTDC",
            "stateMachineContext": {"ftdCDeviceIDs": f"{device['uid']}"},
        }
        CDORequests.put(
            http_session, f"https://{endpoint}", path=f"{CDOAPI.FMC.value}/{cdfmc_specific_device['uid']}", data=data
        )
