from enum import Enum


class CDOAPI(Enum):
    SVCS = "aegis/rest/v1/services"
    DEVICES = f"{SVCS}/targets/devices"
    WORKSET = f"{SVCS}/common/workingset"
    FTDS = f"{SVCS}/firepower/ftds"
    FMC = f"{SVCS}/fmc/appliance"
    OBJS = f"{SVCS}/targets/objects"
    LARS = f"{SVCS}/targets/proxies"
    ASA_CONFIG = f"{SVCS}/asa/configs"
    SPECIFIC_DEVICE = "aegis/rest/v1/device/{uid}/specific-device"
    FMC_ACCESS_POLICY = "fmc/api/fmc_config/v1/domain/{domain_uid}/policy/accesspolicies"
