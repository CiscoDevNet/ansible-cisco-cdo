# -*- coding: utf-8 -*-
#
# Apache License v2.0+ (see LICENSE or https://www.apache.org/licenses/LICENSE-2.0)

from __future__ import absolute_import, division, print_function

__metaclass__ = type

import requests
from ansible_collections.cisco.cdo.plugins.module_utils.cmd.acl import CLIACL
from ansible_collections.cisco.cdo.plugins.module_utils.cmd.acl import CLI


class ApplyTemplate:
    def __init__(self, module_params: dict, http_session: requests.session, endpoint: str) -> None:
        self.results = list()
        self.module_params = module_params
        self.http_session = http_session
        self.endpoint = endpoint

    def apply_access_lists(self) -> None:
        """ACL special handling to replace the existing ACL with a minimal amount of traffic disruption.
        Existing flow will not be interrupted. New flows permitted bu an ACL may be interrupted for milliseconds
        on a per-rule basis."""
        acl_client = CLIACL(self.module_params, self.http_session, self.endpoint)
        acls = acl_client.module_params.get("config").get("access-lists")
        for acl_name, acl_values in acls.items():  # normalize the acl and insert the "no" commands
            running_config_acl = acl_client.get_access_control_list(acl_name)
            acl_client.module_params["cmd_list"] = acl_client.process_access_lists(acl_values, running_config_acl)
            results = acl_client.run_cmd()
            if not results:
                results = "Access-list template(s) appears to have been applied successfully"
            acl_client.results.append(
                {f"{acl_name}_acl_commands_": acl_client.module_params["cmd_list"], "results": results}
            )
            acl_client.prune_acl_lines(acl_name, len(acl_values))
        self.results = self.results + acl_client.results

    def apply_common(self, config_section: str):
        cli_client = CLI(self.module_params, self.http_session, self.endpoint)
        cli_client.module_params["cmd_list"] = list()
        for line in cli_client.module_params.get("config").get(config_section):  # Combine all of the config lines
            cli_client.module_params["cmd_list"].append(line)
        results = cli_client.run_cmd()
        if not results:
            results = f"{config_section} config appears to have been added successfully"
        cli_client.results.append({f"{config_section}": cli_client.module_params["cmd_list"], "results": results})
        self.results = self.results + cli_client.results

    def apply_config(self, sections: list = None):
        """For each of the discreet sections of config, apply them one at a time in a specific order.
        If the sections parameter is passed, only apply that section(s) of the template"""
        if not sections:
            sections = [
                "global",
                "interfaces",
                "static_routes",
                "dns_server_groups",
                "dns_domain-lookup",
                "smart_license",
                "aaa",
                "http",
                "ssh",
                "logging",
                "network_objects",
                "service_objects",
                "ip-pools",
                "access-groups",
                "users",
            ]
            for section in sections:
                self.apply_common(section)
