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
