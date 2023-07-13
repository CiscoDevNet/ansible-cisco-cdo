import urllib.parse


class CDOQuery:
    """ Helpers for building complex inventory queries"""
    @staticmethod
    def get_inventory_query(module_params: dict, extra_filter=None) -> dict:
        """ Build the inventory query based on what the user is looking for"""
        device_type = module_params['device_type']
        filter = module_params['filter']
        r = ("[targets/devices.{name,customLinks,healthStatus,sseDeviceRegistrationToken,"
             "sseDeviceSerialNumberRegistration,sseEnabled,sseDeviceData,state,ignoreCertificate,deviceType,"
             "configState,configProcessingState,model,ipv4,modelNumber,serial,chassisSerial,hasFirepower,"
             "connectivityState,connectivityError,certificate,mostRecentCertificate,tags,tagKeys,type,"
             "associatedDeviceUid,oobDetectionState,enableOobDetection,deviceActivity,softwareVersion,"
             "autoAcceptOobEnabled,oobCheckInterval,larUid,larType,metadata,fmcApplianceIpv4,lastDeployTimestamp}]")

        # Build q query
        if filter is not None and filter != '':
            q = (
                f"( (model:false) AND ( (name:{filter}) OR (ipv4:{filter}) OR (serial:{filter}))) AND (NOT deviceType:FMCE)"
            )
            if extra_filter is not None:
                q = f"{q} {extra_filter}"
        elif device_type is None or device_type == "all":
            q = "(model:false)"
        elif device_type == 'asa' or device_type == 'ios':
            q = f"((model:false) AND (deviceType:{device_type.upper()})) AND (NOT deviceType:FMCE)"
        elif device_type == 'ftd':
            q = ("((model:false) AND ((deviceType:FTD) OR (deviceType:FMC_MANAGED_DEVICE) OR (deviceType:FTDC))) AND "
                 "(NOT deviceType:FMCE)")

        # TODO: add meraki and other types...
        # Build r query
        # if device_type == None or device_type == "meraki" or device_type == "all":
        #    r = r[0:-1] + ",meraki/mxs.{status,state,physicalDevices,boundDevices,network}" + r[-1:]
        return {"q": q, "r": r}

    @staticmethod
    def get_lar_query(module_params: dict) -> str | None:
        # TODO Search for exact match vs the wildcard below
        filter = module_params['sdc']
        if filter is not None:
            return f"name:*{filter}* OR ipv4:*{filter}*"

    @staticmethod
    def get_cdfmc_query() -> str | None:
        return {"q": "deviceType:FMCE"}

    @staticmethod
    def get_cdfmc_policy_query(limit: int, offset: int, access_list_name: str) -> str:
        if access_list_name is not None:
            return f"name={urllib.parse.quote(access_list_name)}"
        else:
            return f"limit={limit}&offset={offset}"
