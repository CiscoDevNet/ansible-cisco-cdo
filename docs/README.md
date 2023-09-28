# Cisco Defense Orchestrator Ansible Collection Sample Playbooks

## Sample usage:
```
ansible-playbook -i inventory.yml -e 'ansible_python_interpreter=/Users/my_user/envs/CDOAnsible/bin/python3' add_asa_ios.yml
```
- `-i inventory.yml` is the path to your inventory file of devices to add
- `add_asa_ios.yml` is the playbook to run against the inventory
- `-e 'ansible_python_interpreter=/Users/my_user/envs/CDOAnsible/bin/python3'` ensures that ansible uses the correct python3 libraries. You may not need this command, but if in doubt, you can always add it with the path to your python3 binary.

## Notes
- Use the sample Ansible inventory file `inventory.yml` for inventory definition examples of devices to add to CDO and general operations
- Use the sample Ansible inventory file `inventory_to_delete.yml` for inventory definition examples of devices to delete from CDO
- Passwords and API keys should NEVER be stored in clear text in inventory or playbooks. Use Ansible vault, environment variables, or other best practices to sote passwords and API keys
- `device_inventory_playbooks/add_asa_ios.yml` and `device_inventory_playbooks/add_ftd.yml` are playbook examples of how to use the sample inventory file `inventory.yml` to add devices to CDO
  - Adds:
    - ASA devices
    - FTD devices, both via CLI ("configure manager" command) and using Low Touch Provisioning (LTP)
    - IOS Devices like Cisco routers and catalyst switches
  - If a device IP/Port/Name already exists in CDO, the device will be skipped and a DuplicateObject error raised and logged to output
- `device_inventory_playbooks/delete_devices.yml` is a playbook example on how to delete devices from CDO using the sample inventory file `inventory_to_delete.yml`
  - Will delete devices by name as defined in the inventory file `inventory_to_delete.yml`
