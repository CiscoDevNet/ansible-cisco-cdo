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
- delete - delete devices from CDO and cdFMC, incuding, ASA, IOS, and FTD devices

v1.0.2
======
- Moved all inventory function into the inventory module and updated the argument spec
- Updated the sample playbooks in /docs

v1.1.0
======
- Breaking Change: Reworked onboarding and inventory
- New module: Deploy - to view and deploy staged ASA changes
- See new sample playbooks and sample inventory
- Updated the sample playbooks in /docs