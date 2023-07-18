# -*- coding: utf-8 -*-
from __future__ import absolute_import, division, print_function
import requests
from ansible_collections.cisco.cdo.plugins.module_utils.query import CDOQuery
from ansible_collections.cisco.cdo.plugins.module_utils.requests import CDORequests
from ansible_collections.cisco.cdo.plugins.module_utils.api_endpoints import CDOAPI
from dataclasses import dataclass, asdict, field

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


# Just toying with the idea of modeling the data
@dataclass
class NetObjContentModel:
    sourceElement: str
    destinationElement: str = None
    type: str = "NetworkContent"

    def asdict(self):
        contents = asdict(self)
        contents["@type"] = contents["type"]
        del contents["type"]
        return contents


@dataclass
class NetObjModel:
    typeName: str
    name: str
    description: str
    stateMachineContext: dict
    contents: NetObjContentModel
    deviceType: str
    objectType: str = "NETWORK_OBJECT"

    def asdict(self):
        net_obj = asdict(self)
        net_obj["@typeName"] = net_obj["typeName"]
        del net_obj["typeName"]
        return net_obj


def get_net_objs(module_params: dict, http_session: requests.session, endpoint: str) -> str:
    # TODO: return only network objects
    q = CDOQuery.net_obj_query(
        filter=module_params["filter"],
        tags=module_params["tags"],
        limit=module_params["limit"],
        offset=module_params["offset"],
    )

    count = CDORequests.get(http_session, f"https://{endpoint}", path=CDOAPI.OBJS.value, query=q | {"agg": "count"})
    logger.debug(f"Count {count}")
    obj_list = CDORequests.get(
        http_session,
        f"https://{endpoint}",
        path=CDOAPI.OBJS.value,
        query=CDOQuery.net_obj_query(
            filter=module_params["filter"],
            tags=module_params["tags"],
            limit=module_params["limit"],
            offset=module_params["offset"],
        ),
    )
    return dict(
        count=count["aggregationQueryResult"],
        limit=module_params["limit"],
        offset=module_params["offset"],
        objects=obj_list,
    )


def add_net_objs(module_params: dict, http_session: requests.session, endpoint: str, data=dict):
    # http_session, f"https://{endpoint}", path=CDOAPI.DEVICES.value, data=ftd_device.asdict()
    new_obj = CDORequests.post(http_session, f"https://{endpoint}", path=CDOAPI.OBJS.value, data=data)
    pass
