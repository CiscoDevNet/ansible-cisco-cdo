# -*- coding: utf-8 -*-
#
# Apache License v2.0+ (see LICENSE or https://www.apache.org/licenses/LICENSE-2.0)

from __future__ import absolute_import, division, print_function

__metaclass__ = type

import urllib.parse


class CDOQuery:
    """Helpers for building complex inventory queries. All parameters for the query should be passed through
    module_params"""

    @staticmethod
    def get_inventory_query(module_params: dict) -> dict:
        """Build the inventory query based on what the user is looking for"""
        device_type = module_params.get("device_type")
        filter = module_params.get("filter")
        r = (
            "[targets/devices.{name,customLinks,healthStatus,sseDeviceRegistrationToken,"
            "sseDeviceSerialNumberRegistration,sseEnabled,sseDeviceData,state,ignoreCertificate,deviceType,"
            "configState,configProcessingState,model,ipv4,modelNumber,serial,chassisSerial,hasFirepower,"
            "connectivityState,connectivityError,certificate,mostRecentCertificate,tags,tagKeys,type,"
            "associatedDeviceUid,oobDetectionState,enableOobDetection,deviceActivity,softwareVersion,"
            "autoAcceptOobEnabled,oobCheckInterval,larUid,larType,metadata,fmcApplianceIpv4,lastDeployTimestamp}]"
        )

        # Build q query
        if device_type is None or device_type == "all":
            q = "((model:false))"
        elif device_type == "asa" or device_type == "ios":
            q = f"((model:false) AND (deviceType:{device_type.upper()})) AND (NOT deviceType:FMCE)"
        elif device_type == "ftd":
            q = (
                "((model:false) AND ((deviceType:FMC_MANAGED_DEVICE) OR (deviceType:FTDC))) AND "
                "(NOT deviceType:FMCE)"
            )
        elif device_type == "fmc":
            q = "deviceType:FMC OR deviceType:FMCE"
        if filter:
            q = q.replace(
                "(model:false)", f"(model:false) AND ((name:{filter}) OR (ipv4:{filter}) OR (serial:{filter}))"
            )
        # TODO: add meraki and other types...
        # Build r query
        # if device_type == None or device_type == "meraki" or device_type == "all":
        #    r = r[0:-1] + ",meraki/mxs.{status,state,physicalDevices,boundDevices,network}" + r[-1:]
        return {"q": q, "r": r}

    @staticmethod
    def get_lar_query(module_params: dict) -> str | None:
        """return a query to retrieve the SDC details"""
        filter = module_params.get("sdc")
        if filter is not None:
            return f"name:{filter} OR ipv4:{filter}"

    @staticmethod
    def get_cdfmc_query() -> dict:
        """Return a query string to retrieve cdFMC information"""
        return {"q": "deviceType:FMCE"}

    @staticmethod
    def get_cdfmc_policy_query(limit: int, offset: int, access_list_name: str) -> str:
        """Return a query to retrieve the given access list name"""
        if access_list_name is not None:
            return f"name={urllib.parse.quote(access_list_name)}"
        else:
            return f"limit={limit}&offset={offset}"

    @staticmethod
    def net_obj_query(name: str = None, network: str = None, tags: list = None) -> dict:
        """Return a query string for network objects given a name, network, or a list of tags"""
        q_part, q = "", ""
        if network is not None:
            q_part = f'(elements:{network.replace("/", "?")})' if "/" in network else f"(elements:{network}?32)"
        if name is not None:
            q_part = f"{q_part} AND (name:{name})" if q_part else f"(name:{name})"
        q = f"(NOT deviceType:FMCE) AND ({q_part})" if q_part else "(NOT deviceType:FMCE)"
        if tags is not None:
            tag_query = " AND ".join(f'tags.labels:"{t}"' for t in tags)
            q = f"{q} AND (({tag_query}))"
        return {"q": q}

    @staticmethod
    def pending_changes_query(module_params: dict, agg: bool = False) -> dict:
        q = (
            f"device.name:{module_params.get('device_name')} AND device.configState:NOT_SYNCED AND device.model:false"
            " AND NOT device.deviceType:FTDC AND NOT device.deviceType:FMC_MANAGED_DEVICE"
        )
        r = "[targets/device-changelog.{changeLogInstance}]"
        if agg:
            return {"agg": "count", "q": q, "resolve": r}
        else:
            return {"limit": module_params.get("limit"), "offset": module_params.get("offset"), "q": q, "resolve": r}

    @staticmethod
    def pending_changes_diff_query(uid: str) -> dict:
        """Given a UID of an Object Reference, generate a query to return the diff details of the config"""
        q = f"(objectReference.uid:{uid})+AND+(changeLogState:ACTIVE)"
        r = "%5Bchangelogs%2Fquery.%7Buid,lastEventTimestamp,changeLogState,events,objectReference%7D%5D"
        return {"q": q, "resolve": r, "limit": 1, "offset": 0}

    @staticmethod
    def cli_executions_query(transaction_id: str) -> dict:
        payload = {
            "q": f"transactionId:{transaction_id}",
            "resolve": (
                "[cli/executions.{createdDate,command,jobUid,deviceUid,transactionId,deviceType,deviceName,"
                "responseHash,executionState,errorMsg}]"
            ),
        }
        return CDOQuery.url_encode_query_data(payload, safe_chars=",-:")

    @staticmethod
    def url_encode_query_data(query_payload: dict, safe_chars: str = "") -> dict:
        encoded_payload = dict()
        for key, value in query_payload.items():
            encoded_payload[key] = urllib.parse.quote_plus(value, safe=safe_chars)
        return encoded_payload

    @staticmethod
    def asa_configs(uid: str) -> dict:
        """Given a UID of an Object Reference, generate a query to return the diff details of the config
                q: uid:070b38b4-5ddf-455c-adfb-075908d6024a
        resolve: [asa/configs.{name,namespace,type,version,state,stateDate,tags,tagKeys,tagValues,asaInterfaces,
        cryptoChecksum,selectedInterfaceObject,selectedInterfaceIP,securityContextMode,metadata}]
        """
        r = (
            "[asa/configs.{name,namespace,type,version,state,stateDate,tags,tagKeys,tagValues,asaInterfaces,"
            "cryptoChecksum,selectedInterfaceObject,selectedInterfaceIP,securityContextMode,metadata}]"
        )
        return CDOQuery.url_encode_query_data({"q": f"uid:{uid}", "resolve": r}, safe_chars=":,")

    @staticmethod
    def device_objects(object_type: str, working_set: str, limit=50, offset=0) -> dict:
        """Generate a query by object-name that return objects for a specific device
        Object types:[NETWORK, PROTOCOL, SERVICE, ICMP, URL]"""

        return {
            "q": (
                f"((cdoInternal:false) AND (isReadOnly:false OR metadata.CDO_FMC_READONLY:true OR objectType:SGT_GROUP)) "
                'AND ((objectType:*{object_type}*)) AND (references:"$isNull") AND (NOT deviceType:FMC_MANAGED_DEVICE AND '
                "NOT deviceType:FMC)"
            ),
            "workingSet": working_set,
            "sort": "name:asc",
            "limit": limit,
            "offset": offset,
        }

    @staticmethod
    def config_summaries(uid: str) -> dict:
        return {"q": f"deviceUid:{uid}", "resolve": "%5Bftd%2Fsummaries.%7BstagedConfigurationUid%7D%5D"}

    @staticmethod
    def access_policy(ruleset_uid: str, limit: int = 50, offset: int = 0, sort: str = "index:asc") -> dict:
        return {
            "q": f"ruleSetUid:{ruleset_uid}",
            "sort": sort,
            "offset": offset,
            "limit": limit,
        }

    @staticmethod
    def rulesets(configuration_uid: str, name: str = "", count: bool = True) -> dict:
        query = {"q": ""}
        query["q"] = f"configurationUid:{configuration_uid}"
        if name:
            query["q"] += f" AND name:{name}"
        elif count:
            query["agg"] = "count"
        return query
