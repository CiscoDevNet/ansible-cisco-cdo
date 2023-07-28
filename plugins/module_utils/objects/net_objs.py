#!/usr/bin/python
# -*- coding: utf-8 -*-
#
# Apache License v2.0+ (see LICENSE or https://www.apache.org/licenses/LICENSE-2.0)

from __future__ import absolute_import, division, print_function

__metaclass__ = type

import requests
from ansible_collections.cisco.cdo.plugins.module_utils.query import CDOQuery
from ansible_collections.cisco.cdo.plugins.module_utils.requests import CDORequests
from ansible_collections.cisco.cdo.plugins.module_utils.api_endpoints import CDOAPI
from ansible_collections.cisco.cdo.plugins.module_utils.errors import DuplicateObject

__metaclass__ = type

# fmt: off
# Remove for publishing....
import logging
logging.basicConfig()
logger = logging.getLogger('net_obj')
fh = logging.FileHandler('/tmp/net_obj.log')
fh.setLevel(logging.DEBUG)
logger.setLevel(logging.DEBUG)
logger.addHandler(fh)
logger.debug("Logger started......")
# fmt: on


def get_net_objs_count(query: dict, http_session: requests.session, endpoint: str) -> int:
    return CDORequests.get(
        http_session, f"https://{endpoint}", path=CDOAPI.OBJS.value, query=query | {"agg": "count"}
    ).get("aggregationQueryResult")


def get_net_objs(module_params: dict, http_session: requests.session, endpoint: str) -> str:
    # TODO: Handle paging (limit, offset)
    q = CDOQuery.net_obj_query(
        name=module_params.get("name"),
        network=module_params.get("network"),
        tags=module_params.get("tags"),
    )
    count = get_net_objs_count(q | {"agg": "count"}, http_session, endpoint)
    if count:
        obj_list = CDORequests.get(
            http_session,
            f"https://{endpoint}",
            path=CDOAPI.OBJS.value,
            query=q | {"limit": module_params.get("limit"), "offset": module_params.get("offset")},
        )
        logger.debug(f"Return: {obj_list}")
        logger.debug
        return dict(
            count=count,
            limit=module_params.get("limit"),
            offset=module_params.get("offset"),
            objects=obj_list,
        )
    else:
        return {}


def is_object_exists(module_params: dict, http_session: requests.session, endpoint: str):
    q = CDOQuery.net_obj_query(
        name=module_params.get("name"),
        network=module_params.get("network"),
        tags=module_params.get("tags"),
    )
    return True if get_net_objs_count(q | {"agg": "count"}, http_session, endpoint) else False


def add_net_objs(module_params: dict, http_session: requests.session, endpoint: str):
    logger.debug(f'Description is {module_params.get("description")}')
    if not is_object_exists(module_params, http_session, endpoint):
        net_obj = {
            "@typeName": "LocalObject",
            "objectType": "NETWORK_OBJECT",
            "stateMachineContext": {},
            "contents": [
                {"@type": "NetworkContent", "sourceElement": module_params.get("network"), "destinationElement": None}
            ],
            "name": module_params.get("name"),
            "description": module_params.get("description"),
            "deviceType": "ASA",
        }
        return CDORequests.post(http_session, f"https://{endpoint}", path=CDOAPI.OBJS.value, data=net_obj)
    else:
        raise DuplicateObject(
            f'Network Object named {module_params.get("name")} with value {module_params.get("network")} already exists'
        )
