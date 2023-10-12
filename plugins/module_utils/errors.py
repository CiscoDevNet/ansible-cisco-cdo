#!/usr/bin/python
# -*- coding: utf-8 -*-
#
# Apache License v2.0+ (see LICENSE or https://www.apache.org/licenses/LICENSE-2.0)

from __future__ import absolute_import, division, print_function

__metaclass__ = type


class DuplicateObject(Exception):
    def __init__(self, message):
        self.message = message
        super().__init__(self.message)


class DeviceUnreachable(Exception):
    def __init__(self, message):
        self.message = message
        super().__init__(self.message)


class UntrustedCertificate(Exception):
    def __init__(self, message):
        self.message = message
        super().__init__(self.message)


class SDCNotFound(Exception):
    def __init__(self, message):
        self.message = message
        super().__init__(self.message)


class AddDeviceFailure(Exception):
    def __init__(self, message):
        self.message = message
        super().__init__(self.message)


class CredentialsFailure(Exception):
    def __init__(self, message):
        self.message = message
        super().__init__(self.message)


class DeviceNotFound(Exception):
    def __init__(self, message):
        self.message = message
        super().__init__(self.message)


class TooManyMatches(Exception):
    def __init__(self, message):
        self.message = message
        super().__init__(self.message)


class ObjectNotFound(Exception):
    def __init__(self, message):
        self.message = message
        super().__init__(self.message)


class APIError(Exception):
    def __init__(self, message):
        self.message = message
        super().__init__(self.message)


class InvalidCertificate(Exception):
    def __init__(self, message):
        self.message = message
        super().__init__(self.message)


class RetriesExceeded(Exception):
    def __init__(self, message):
        self.message = message
        super().__init__(self.message)


class CmdExecutionError(Exception):
    def __init__(self, message):
        self.message = message
        super().__init__(self.message)


class DeviceNotInSync(Exception):
    def __init__(self, message):
        self.message = message
        super().__init__(self.message)
