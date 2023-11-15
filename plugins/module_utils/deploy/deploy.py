# -*- coding: utf-8 -*-
#
# Apache License v2.0+ (see LICENSE or https://www.apache.org/licenses/LICENSE-2.0)


from __future__ import absolute_import, division, print_function

__metaclass__ = type

# fmt: off
import requests
import time
from time import sleep
from ansible_collections.cisco.cdo.plugins.module_utils.api_endpoints import CDOAPI
from ansible_collections.cisco.cdo.plugins.module_utils.api_requests import CDORequests
from ansible_collections.cisco.cdo.plugins.module_utils._version import __version__
from ansible_collections.cisco.cdo.plugins.module_utils.query import CDOQuery
from ansible_collections.cisco.cdo.plugins.module_utils.device_inventory.inventory import Inventory
from ansible_collections.cisco.cdo.plugins.module_utils.errors import DeviceNotFound, TooManyMatches
# fmt: on

# TODO: Document and Link with cdFMC Ansible module to deploy staged FTD configs

# fmt: off
# Remove for publishing....
import logging
logging.basicConfig()
logger = logging.getLogger('cmd')
fh = logging.FileHandler('/tmp/deploy.log')
fh.setLevel(logging.DEBUG)
logger.setLevel(logging.DEBUG)
logger.addHandler(fh)
logger.debug("Logger started deploy.py......")
# fmt: on


class Deploy:
    def __init__(self, module_params: dict, http_session: requests.session, endpoint: str):
        logger.debug(f"init: module_params: {module_params}")
        self.module_params = module_params
        self.http_session = http_session
        self.endpoint = endpoint
        self.inventory_client = Inventory(module_params, http_session, endpoint)
        self.changed = False
        self.pending_changes = None

    def poll_deploy_job(self, job_uid: str, retry, interval):
        """Poll the deploy job for a successful completion"""
        while retry > 0:
            job_status = CDORequests.get(
                self.http_session, f"https://{self.endpoint}", path=f"{CDOAPI.JOBS.value}/{job_uid}"
            )
            state_uid = job_status.get("objRefs")[0].get("uid")
            if job_status.get("stateMachinesProgress").get(state_uid).get("progressStatus") == "DONE":
                return job_status
            sleep(interval)
            retry -= 1

    def deploy_changes(self):
        """Given the device name, deploy the pending config changes to the device if there are any"""

        # Check to see if there are any pending changes before deploying unnecessarily
        q = CDOQuery.pending_changes_query(self.module_params, agg=True)
        count = CDORequests.get(
            self.http_session, f"https://{self.endpoint}", path=f"{CDOAPI.DEPLOY.value}", query=q
        ).get("aggregationQueryResult")
        if not count:
            return

        # collect the pending changes before deployment
        pending_config = self.get_pending_deploy()

        # Deploy the pending config
        self.module_params["filter"] = self.module_params.get("device_name")
        device = self.inventory_client.gather_inventory()
        if len(device) == 0:
            raise (DeviceNotFound(f"Could not find device {self.module_params.get('device_name')}"))
        elif len(device) == 0:
            raise (
                TooManyMatches(
                    f"{len(device)} matched - {self.module_params.get('device_name')} not a unique device name"
                )
            )
        payload = {
            "action": "WRITE",
            "overallProgress": "PENDING",
            "triggerState": "PENDING_ORCHESTRATION",
            "schedule": None,
            "objRefs": [{"uid": device[0].get("uid"), "namespace": "targets", "type": "devices"}],
            "jobContext": None,
        }

        # Submit the job then return the completed job details after polling for deploy completion
        job = CDORequests.post(self.http_session, f"https://{self.endpoint}", path=f"{CDOAPI.JOBS.value}", data=payload)

        return {
            "deploy_job": self.poll_deploy_job(
                job.get("uid"), self.module_params.get("timeout"), self.module_params.get("interval")
            ),
            "changes_deployed": pending_config,
        }

    def get_pending_deploy(self) -> str:
        """Given a device name, return the config staged in CDO to be deployed, if any"""
        logger.debug(f"module parameters: {self.module_params}")
        pending_change = list()
        q = CDOQuery.pending_changes_query(self.module_params)
        result = CDORequests.get(self.http_session, f"https://{self.endpoint}", path=f"{CDOAPI.DEPLOY.value}", query=q)
        for item in result:
            staged_config = dict()
            staged_config["device_uid"] = item.get("changeLogInstance").get("objectReference").get("uid")
            staged_config["device"] = item.get("changeLogInstance").get("name")
            staged_config["diff"] = list()
            for event in item.get("changeLogInstance").get("events"):
                event.get("details").pop("_class")
                staged_config["diff"].append(event.get("details"))
                staged_config["user"] = event.get("user")
                staged_config["date"] = (
                    time.strftime("%Y-%m-%d %H:%M:%S", time.gmtime(int(event.get("eventDate")) / 1000.0)) + " UTC"
                )
                staged_config["action"] = event.get("action")
            pending_change.append(staged_config)
        logger.debug(f"pending_change: {pending_change}")
        return pending_change
