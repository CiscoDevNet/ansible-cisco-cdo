==================================
Cisco CDO Collection Release Notes
==================================
.. contents:: Topics

v1.0.0
======

New Modules
-----------
- inventory - list CDO device inventory for ASA, IOS, FTD, FMC, and cdFMC
- add_asa_ios - Add ASA and IOS devices to CDO
- add_ftd - Add FTD devices to CDO using both "configure manager" cli method and low touch provisioning
- delete - delete devices from CDO and cdFMC, including, ASA, IOS, and FTD devices

v1.0.2
======
- Moved all inventory function into the inventory module and updated the argument spec
- Updated the sample playbooks in /docs

v1.1.0
======
- Breaking Change: Reworked onboarding and inventory
- See new sample playbooks and sample inventory
- Updated the sample playbooks in /docs

New Modules
-----------
- deploy - view and deploy staged ASA changes per device

v1.1.1
======
- Added error handling for an invalid API key to pass back to a playbook

v1.1.2
======
- Bugfix adding LTP device with no password caused an error in a CDO workflow
- Updated LTP sample playbook to add password if it is in inventory else none

v1.1.3
======
Documentation corrections

v1.1.4
======
Fixed an issue where onboarding an LTP firewall could result in a 404 error
