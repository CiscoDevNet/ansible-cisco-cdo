# -*- coding: utf-8 -*-
#
# Apache License v2.0+ (see LICENSE or https://www.apache.org/licenses/LICENSE-2.0)

from __future__ import absolute_import, division, print_function

__metaclass__ = type

from typing import Optional
from dataclasses import dataclass
from dataclasses_json import dataclass_json


@dataclass_json
@dataclass
class Device:
    anyConnectCertExpDate: str
    chassisSerial: str
    configState: str
    connectivityError: str
    connectivityState: str
    customLinks: str
    deviceType: str
    host: str
    ipv4: str
    lastDeployTimestamp: str
    larType: str
    modelNumber: str
    name: str
    oobDetectionState: str
    port: str
    serial: str
    softwareVersion: str
    tags: dict
    tagKeys: list
    tagValues: list
    uid: str


@dataclass_json
@dataclass
class FMC(Device):
    sseDeviceData: dict


@dataclass_json
@dataclass
class FTD(Device):
    associatedDeviceUid: str
    metadata: dict
    healthStatus: str


@dataclass_json
@dataclass
class ASA(Device):
    liveAsaDevice: bool
    asaInterfaces: Optional[list] = None
    licenseFeatures: Optional[dict] = None
    failover: Optional[str] = None
    failoverMode: Optional[str] = None
    failoverStateThis: Optional[str] = None
    failoverStateOther: Optional[str] = None
    failoverPrimaryState: Optional[str] = None
    failoverSecondaryState: Optional[str] = None
    failoverMateVersion: Optional[str] = None
    failoverMateSerialNumber: Optional[str] = None
    contextMode: Optional[str] = None
    uptimeHumanReadable: Optional[str] = None
