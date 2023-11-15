# -*- coding: utf-8 -*-
#
# Apache License v2.0+ (see LICENSE or https://www.apache.org/licenses/LICENSE-2.0)

from __future__ import absolute_import, division, print_function

__metaclass__ = type

import re

from ansible_collections.cisco.cdo.plugins.module_utils.cmd.cli import CLI


class CLIACL(CLI):
    """This class extends the CLI class to process ACL templates"""

    def get_access_control_list(self, acl_name: str) -> list:
        """
        Given an ACL name from an ASA, return the running-config for that ACL.
        If the ACL is not found, return an empty list
        """
        results = self.get_running_config(extra_parameter=f"access-list {acl_name}")
        if len(results) == 1 and results[0].startswith("ERROR:"):  # The acl does not exist
            return []
        return results

    def process_access_lists(self, access_list: list, running_config_acl: bool):
        """If the acl exists, we need to attempt remove the existing entry to avoid CLI errors. Then add line numbers to
        each acl entry to ensure the correct order
        """
        acl_commands = []
        for line in access_list:  # Loop through the template ACL
            no_line_num = re.sub(r"(^access-list\s[A-z'-_]+)(\sline\s\d+)?([\s\S]*)", r"\1\3", line)  # del line #
            for running_line in running_config_acl:  # Loop through the device's ACL
                if self.is_ace_exists(no_line_num, running_line):
                    acl_commands.append(f"no {no_line_num}")
            acl_commands.append(line)
        return acl_commands

    def is_ace_exists(self, ace_1: str, ace_2: str) -> bool:
        """Given an ACE, check to see if some form of the ACE exists in the the other ACE"""
        pattern = r"\slog.+|\sinactive.*|\stime-range.*"  # remove the optional parameters for an ACL entry on ASA
        normalized_ace_1 = re.sub(pattern, "", ace_1, flags=re.I).strip()
        normalized_ace_2 = re.sub(pattern, "", ace_2, flags=re.I).strip()
        return True if normalized_ace_1 == normalized_ace_2 else False

    def prune_acl_lines(self, acl_name: list, acl_template_len: int):
        """Remove ACL lines that are left over after prepending the template to the ACL"""
        current_acl = self.get_access_control_list(acl_name)
        self.module_params["cmd_list"] = []
        for line in current_acl[acl_template_len:]:
            self.module_params["cmd_list"].append(f"no {line}")
        if self.module_params["cmd_list"]:
            results = self.run_cmd()
            if not results:
                results = "ACL cleanup appears to have completed successfully"
            self.results.append({"commands": self.module_params["cmd_list"], "results": results})
