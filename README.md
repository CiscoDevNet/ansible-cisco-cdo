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

### Cisco Defense Orcestrator API Key
This module is for interacting with the Cisco Defense Orcestrator (CDO) platform and as such the module requires a CDO API key for each CDO tenant in which you wish to operate. It is STRONGLY recommneded that you do NOT store your API key or other passwords in your playbooks. Use environment variables, ansible vault, or other best practices for safe password/API key usage.
In the sample playbooks under `/docs`, we are getting this API key from an environment variable. You will also need to supply the CDO regional instance where this API key was generated (us, eu, apj). In a bash shell, you will add something like this to your `.bashrc` file or other bash profile settings:
```
export CDO_API_KEY="xxxxx"
export CDO_REGION="us"
```

## Included content
<!--start collection content-->
### Modules
| Name             | Description                                             |
| ---------------- | ------------------------------------------------------- |
| device_inventory | gather, add, or delete an FTD, ASA or IOS device to CDO |
| deploy           | Deploy staged ASA or IOS configurations to live devices |
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
See the docs directory and README for practical usage of this collection.

## Contributing to this collection
We welcome community contributions to this collection. If you find problems, please open an issue or create a PR against the [Cisco Defense Orchestrator collection repository](https://github.com/CiscoDevNet/ansible-cisco-cdo). See [Contributing to Ansible-maintained collections](https://docs.ansible.com/ansible/devel/community/contributing_maintained_collections.html#contributing-maintained-collections) for complete details.

### Code of Conduct
This collection follows the Ansible project's
[Code of Conduct](https://docs.ansible.com/ansible/devel/community/code_of_conduct.html).
Please read and familiarize yourself with this document.

## Release notes
Release notes are available [here](https://github.com/CiscoDevNet/ansible-cisco-cdo/blob/main/CHANGELOG.rst).

## Roadmap
Additional modules will be added in future releases. These include:
- objects and object-groups operations
- policy operations
- multi-tenant operations
- log searching operations
- VPN operations
- others tbd

## Licensing
Apache License Version 2.0 or later.
See [LICENSE](https://www.apache.org/licenses/LICENSE-2.0) to see the full text.
