# Ansible Collection - cisco.cdo

# CISCO CDO Ansible Collection

The Ansible Cisco CDO collection includes a variety of Ansible content to help automate the interaction with the Cisco Defense Orcestrator (CDO) platform and the devices managed by the CDO platform.

This is a work in progress and more modules and functionality will be added in subsequent releases.

## Ansible version compatibility

This collection has been tested against following Ansible versions: **>=2.9.10** and should work in 2.9+

## External requirements
### Python libraries
The needed python libraries are in requirements.txt
```
pip3 install -r requirements.txt
```
or
```
pip3 install pycryptodome requests jmespath
```

### Cisco Defense Orcestrator API Key
This module is for interacting with the Cisco Defense Orcestrator (CDO) platform and as such the module requires a CDO API key for each CDO tenant in which the user wishes to operate. It is STRONGLY recommneded that you do NOT store your API key or other passwords in your playbooks. Use environment variables, ansible vault, or other best practices for safe password/API key usage.

## Included content
<!--start collection content-->
### Modules
Name | Description
--- | ---
add_asa_ios | Add an ASA or IOS device to CDO
add_ftd | Add an FTD to CDO by `configure manager` or `low touch provisioning`
delete | Remove an FTD, ASA, or IOS device from CDO
inventory | Get device details from CDO
<!--end collection content-->
   
## Installing this collection
You can install the Cisco CDO collection with the Ansible Galaxy CLI:

    ansible-galaxy collection install cisco.cdo
    
You can also include it in a `requirements.yml` file and install it with `ansible-galaxy collection install -r requirements.yml`, using the format:

```yaml
---
collections:
  - name: cisco.cdo
```
## Using the collection
**"Show don't tell"**  
See the samples directory and README for practical usage of this collection.

## Contributing to this collection
We welcome community contributions to this collection. If you find problems, please open an issue or create a PR against the [Cisco Defense Orchestrator collection repository](https://github.com/CiscoDevNet/ansible-cisco-cdo). See [Contributing to Ansible-maintained collections](https://docs.ansible.com/ansible/devel/community/contributing_maintained_collections.html#contributing-maintained-collections) for complete details.

### Code of Conduct
This collection follows the Ansible project's
[Code of Conduct](https://docs.ansible.com/ansible/devel/community/code_of_conduct.html).
Please read and familiarize yourself with this document.

## Release notes
<!--Add a link to a changelog.md file or an external docsite to cover this information. -->
Release notes are available [here](https://github.com/CiscoDevNet/ansible-cisco-cdo/CHANGELOG.rst).

## Roadmap
Additional modules will be added in future releases. These include:
- objects and object-groups
- multi-tenant
- policy
- others tbd
<!-- Optional. Include the roadmap for this collection, and the proposed release/versioning strategy so users can anticipate the upgrade/update cycle. -->
## Licensing
Apache License Version 2.0 or later.
See [LICENSE](https://www.apache.org/licenses/LICENSE-2.0) to see the full text.
