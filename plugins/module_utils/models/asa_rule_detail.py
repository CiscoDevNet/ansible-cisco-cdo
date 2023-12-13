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
    name: Optional[str] = None
    uid: Optional[str] = None
    type: Optional[str] = None
    elements: Optional[str] = None


@dataclass_json
@dataclass
class AsaRuleDetails:
    # note: if uid and type is None, we are working with inline IP addresses
    # Build the ansible input based on this model....
    ruleAction: Optional[str] = None
    active: Optional[bool] = True
    protocol: Optional[ObjectReferenceContentWithElements] = None
    sourcePort: Optional[ObjectReferenceContentWithElements] = None
    sourceNetwork: Optional[ObjectReferenceContentWithElements] = None
    destinationPort: Optional[ObjectReferenceContentWithElements] = None
    destinationNetwork: Optional[ObjectReferenceContentWithElements] = None
    sourceDynamicObject: Optional[str] = None
    destinationDynamicObject: Optional[str] = None
    icmpArgument: Optional[str] = None
    isActive: Optional[str] = None
    remark: Optional[str] = None
    timerange: Optional[str] = None
    logSettings: Optional[dict] = None


@dataclass_json
@dataclass
class FirewallRule(AsaRuleDetails):
    ruleType: Optional[str] = None
    index: Optional[int] = None
    ruleDetails: Optional[AsaRuleDetails] = None
    configurationUid: Optional[str] = None
    ruleSetUid: Optional[str] = None
