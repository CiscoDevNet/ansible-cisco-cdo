# -*- coding: utf-8 -*-
#
# Apache License v2.0+ (see LICENSE or https://www.apache.org/licenses/LICENSE-2.0)

from __future__ import absolute_import, division, print_function

__metaclass__ = type

from enum import Enum


class CDOAPI(Enum):
    AEGIS = "aegis/rest/v1"
    ASA_CONFIGS = f"{AEGIS}/services/asa/configs"
    ASA_DEVICE_CONFIGS = f"{AEGIS}/services/asa/devices-configs"
    CONFIG_SUMMARIES = f"{AEGIS}/services/ftd/summaries"
    CLI_EXECUTIONS = f"{AEGIS}/services/cli/executions"
    DEPLOY = f"{AEGIS}/services/targets/device-changelog"
    DEVICES = f"{AEGIS}/services/targets/devices"
    FEATURES = f"{AEGIS}/features"
    FIREWALL_RULES = f"{AEGIS}/services/targets/firewallrules"
    FMC = f"{AEGIS}/services/fmc/appliance"
    FMC_ACCESS_POLICY = "fmc/api/fmc_config/v1/domain/{domain_uid}/policy/accesspolicies"  # {domain_uid} when using
    FTDS = f"{AEGIS}/services/firepower/ftds"
    JOBS = f"{AEGIS}/services/state-machines/jobs"
    LARS = f"{AEGIS}/services/targets/proxies"
    OBJS = f"{AEGIS}/services/targets/objects"
    RULESETS = f"{AEGIS}/services/targets/rulesets"
    SPECIFIC_DEVICE = f"{AEGIS}/device/{{uid}}/specific-device"  # {UID} with be replaced when using
    WORKSET = f"{AEGIS}/services/common/workingset"
    USERS = "anubis/rest/v1/users"
