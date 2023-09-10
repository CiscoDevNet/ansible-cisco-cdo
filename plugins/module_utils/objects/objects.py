#!/usr/bin/python
# -*- coding: utf-8 -*-
#
# Apache License v2.0+ (see LICENSE or https://www.apache.org/licenses/LICENSE-2.0)

from __future__ import absolute_import, division, print_function

__metaclass__ = type

import requests
from ansible_collections.cisco.cdo.plugins.module_utils.requests import CDORequests
from ansible_collections.cisco.cdo.plugins.module_utils.api_endpoints import CDOAPI
from ansible_collections.cisco.cdo.plugins.module_utils.query import CDOQuery

# fmt: off
# Remove for publishing....
import logging
logging.basicConfig()
logger = logging.getLogger('obj')
fh = logging.FileHandler('/tmp/net_obj.log')
fh.setLevel(logging.DEBUG)
logger.setLevel(logging.DEBUG)
logger.addHandler(fh)
logger.debug("Logger started......")
# fmt: on


def get_objs_count(query: dict, http_session: requests.session, endpoint: str) -> int:
    return CDORequests.get(
        http_session, f"https://{endpoint}", path=CDOAPI.OBJS.value, query=query | {"agg": "count"}
    ).get("aggregationQueryResult")


def get_objs(q: str, http_session: requests.session, endpoint: str, limit: int = 50, offset: int = 0) -> str:
    count = get_objs_count(q, http_session, endpoint)
    if count:
        obj_list = CDORequests.get(
            http_session,
            f"https://{endpoint}",
            path=CDOAPI.OBJS.value,
            query=q | {"limit": limit, "offset": offset},
        )
        logger.debug(f"Return: {obj_list}")
        logger.debug
        return dict(
            count=count,
            limit=limit,
            offset=offset,
            objects=obj_list,
        )
    else:
        return {}
