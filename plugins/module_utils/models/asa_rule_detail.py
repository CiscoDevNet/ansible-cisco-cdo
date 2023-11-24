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
class ObjectReferenceContentWithElements:
    name: str
    uid: str
    type: str
    elements: list


@dataclass_json
@dataclass
class AsaRuleDetails:
    # note: if uid and type is null, we are working with inline IP addresses
    # Build the ansible input based on this model....
    ruleAction: str
    protocol: ObjectReferenceContentWithElements
    sourcePort: ObjectReferenceContentWithElements
    sourceNetwork: ObjectReferenceContentWithElements
    destinationPort: ObjectReferenceContentWithElements
    destinationNetwork: ObjectReferenceContentWithElements
    active: bool
    sourceDynamicObject: Optional[str] = None
    destinationDynamicObject: Optional[str] = None
    icmpArgument: Optional[str] = None
    isActive: Optional[str] = None
    remark: Optional[str] = None
    timerange: Optional[str] = None
    logSettings: Optional[dict] = None


@dataclass_json
@dataclass
class FirewallRule:
    ruleType: str
    index: int
    ruleDetails: AsaRuleDetails
    configurationUid: str
    ruleSetUid: str
