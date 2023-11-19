# -*- coding: utf-8 -*-
#
# Apache License v2.0+ (see LICENSE or https://www.apache.org/licenses/LICENSE-2.0)


from __future__ import absolute_import, division, print_function

__metaclass__ = type

import requests
from ansible_collections.cisco.cdo.plugins.module_utils.api_endpoints import CDOAPI
from ansible_collections.cisco.cdo.plugins.module_utils.api_requests import CDORequests
from ansible_collections.cisco.cdo.plugins.module_utils.tenant.tenant import Tenant
from ansible_collections.cisco.cdo.plugins.module_utils.query import CDOQuery


# fmt: off
# Remove for publishing....
import logging
logging.basicConfig()
logger = logging.getLogger('config')
fh = logging.FileHandler('/tmp/config.log')
fh.setLevel(logging.DEBUG)
logger.setLevel(logging.DEBUG)
logger.addHandler(fh)
logger.debug("config.log logger started......")
# fmt: on


class Config:
    def __init__(self, module_params: dict, http_session: requests.session, endpoint: str) -> None:
        self.module_params = module_params
        self.http_session = http_session
        self.endpoint = endpoint
        self.asa_config_new_model = False
        self.get_cdo_asa_model_type()

    def get_asa_config(self):
        if self.get_cdo_asa_model_type():
            # new model
            pass
        else:
            # old model
            pass

    def get_asa_config_old_model(self):
        """For the "old" ASA model, return the ASA (CDO) configuration"""
        logger.debug(f"device uid type: {type(self.module_params)}")
        logger.debug(f"device uid: {self.module_params.get('device_uid')}")
        device_data = CDORequests.get(
            self.http_session,
            f"https://{self.endpoint}",
            path=f"{CDOAPI.DEVICES.value}/{self.module_params.get('device_uid')}",
        )
        logger.debug(f"ASA Config: {device_data.get('deviceConfig')}")
        return device_data.get("deviceConfig")

    def get_cdo_asa_model_type(self):
        """Determine if the tenant is using the old ASA data model or the new ASA data model"""
        tenant_info = Tenant(self.module_params, self.http_session, self.endpoint)
        return True if tenant_info.get_features().get("asa_configuration_object_migration") else False

    def get_asa_devices_configs(self) -> list:
        """CDO API ../asa/devices-configs returns the configuration uid of the
        current configurations that are associated with the device uid"""
        query = CDOQuery.url_encode_query_data(
            {"q": f"source.uid:{self.module_params.get('device_uid')}"}, safe_chars=":"
        )
        device_configs = CDORequests.get(
            self.http_session, f"https://{self.endpoint}", path=f"{CDOAPI.ASA_DEVICE_CONFIGS.value}", query=query
        )
        logger.debug(f"get_asa_devices_configs {device_configs}")
        return device_configs

    def get_asa_configs(self) -> list:
        # TODO: Add this to the inventory output!
        """Given a target uid from self.get_asa_devices_configs() return portion of the current configuration"""
        return self.get_asa_config_old_model()
        # asa_configs = list()
        # asa_device_configs = self.get_asa_devices_configs()
        # for asa_device_config in asa_device_configs:
        #     target_uid = asa_device_config.get("target").get("uid")
        #     query = CDOQuery.asa_configs(target_uid)
        #     asa_configs.append(
        #         CDORequests.get(
        #             self.http_session, f"https://{self.endpoint}", path=f"{CDOAPI.ASA_CONFIGS.value}", query=query
        #         )
        #     )
        # return asa_configs
