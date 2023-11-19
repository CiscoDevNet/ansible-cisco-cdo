# -*- coding: utf-8 -*-
#
# Apache License v2.0+ (see LICENSE or https://www.apache.org/licenses/LICENSE-2.0)

from __future__ import absolute_import, division, print_function

__metaclass__ = type

import requests
from ansible_collections.cisco.cdo.plugins.module_utils.api_endpoints import CDOAPI
from ansible_collections.cisco.cdo.plugins.module_utils.query import CDOQuery
from ansible_collections.cisco.cdo.plugins.module_utils.api_requests import CDORequests
from ansible_collections.cisco.cdo.plugins.module_utils.errors import DeviceNotFound, ObjectNotFound

# fmt: off
# Remove for publishing....
import logging
logging.basicConfig()
logger = logging.getLogger('tenant')
fh = logging.FileHandler('/tmp/tenant.log')
fh.setLevel(logging.DEBUG)
logger.setLevel(logging.DEBUG)
logger.addHandler(fh)
logger.debug("tenant.log logger started......")
# fmt: on


class Tenant:
    def __init__(self, module_params: dict, http_session: requests.session, endpoint: str) -> None:
        self.module_params = module_params
        self.http_session = http_session
        self.endpoint = endpoint
        self.features = None

    def get_features(self):
        logger.debug(f"get features: {self.module_params}")
        return CDORequests.get(self.http_session, f"https://{self.endpoint}", path=f"{CDOAPI.FEATURES.value}")

    def get_users(self):
        logger.debug(f"get features: {self.module_params}")
        return CDORequests.get(self.http_session, f"https://{self.endpoint}", path=f"{CDOAPI.USERS.value}")
