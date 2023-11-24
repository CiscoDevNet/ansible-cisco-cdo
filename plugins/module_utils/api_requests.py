# -*- coding: utf-8 -*-
#
# Apache License v2.0+ (see LICENSE or https://www.apache.org/licenses/LICENSE-2.0)

from __future__ import absolute_import, division, print_function

__metaclass__ = type

import requests
from enum import Enum
from functools import wraps
from .errors import DuplicateObject, APIError, DeviceNotFound, CredentialsFailure


class CDORegions(Enum):
    """CDO API Endpoints by Region"""

    us = "www.defenseorchestrator.com"
    eu = "www.defenseorchestrator.eu"
    apj = "apj.cdo.cisco.com"


class CDOAPIWrapper(object):
    """This decorator class wraps all API methods of ths client and solves a number of issues. For example, if an
    object already exists when attempting to create an object, raise the custom error 'CDODuplicateDevice' and give
    the consumer the opportunity to ignore the error and carry on with other operations in their script.
    Note that the response from the API calls are a tuple. Example:
    """

    def __call__(self, fn):
        @wraps(fn)
        def new_func(*args, **kwargs):
            try:
                return fn(*args, **kwargs)
            except requests.HTTPError as ex:
                if ex.response.status_code == 404:
                    raise DeviceNotFound("404 Device Not Found")
                elif ex.response.status_code == 401:
                    raise CredentialsFailure("API Key was rejected by CDO API")
                elif ex.response.status_code in range(400, 600):
                    if "Duplicate" in ex.response.text:
                        raise DuplicateObject(ex.response.text)
                    else:
                        raise APIError(ex)

        return new_func


class CDORequests:
    @staticmethod
    def create_session(token: str, version: str) -> requests.Session:
        """Helper function to set the auth token and accept headers in the API request"""
        http_session = requests.Session()
        http_session.headers = {
            "Authorization": f"Bearer {token.strip()}",
            "Accept": "*/*",
            "Content-Type": "application/json",
            "User-Agent": f"AnsibleCDOModule/{version}",
        }
        return http_session

    @CDOAPIWrapper()
    @staticmethod
    def get(http_session: requests.Session, url: str, path: str = None, query: dict = None) -> dict | list:
        """Given the CDO endpoint, path, and query, return the json payload from the API"""
        # TODO: convert dictionary of query to encoded string with safe values..
        # params = urllib.parse.quote(query.encode('utf-8'), safe='()/')
        uri = url if path is None else f"{url}/{path}"
        result = http_session.get(
            url=uri,
            headers=http_session.headers,
            params=query,
        )
        result.raise_for_status()
        if result.json():
            return result.json()

    @CDOAPIWrapper()
    @staticmethod
    def post(http_session: requests.Session, url: str, path: str = None, data: dict = None, query: dict = None) -> dict:
        """Given the CDO endpoint, path, and query, post the json data and return the json payload from the API"""
        uri = url if path is None else f"{url}/{path}"
        result = http_session.post(url=uri, params=query, json=data)
        result.raise_for_status()
        if result.text and result.status_code in range(200, 300):
            return result.json()

    @CDOAPIWrapper()
    @staticmethod
    def put(http_session: requests.Session, url: str, path: str = None, data: dict = None, query: dict = None) -> dict:
        """Given the CDO endpoint, path, and query, return the json payload from the API"""
        uri = url if path is None else f"{url}/{path}"
        result = http_session.put(url=uri, headers=http_session.headers, params=query, json=data)
        result.raise_for_status()
        if result.text and result.status_code in range(200, 300):
            return result.json()

    @CDOAPIWrapper()
    @staticmethod
    def delete(http_session: requests.Session, url: str, path: str = None) -> int:
        result = http_session.delete(url=f"{url}/{path}", headers=http_session.headers)
        result.raise_for_status()
        return result.status_code
