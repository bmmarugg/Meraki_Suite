import meraki
from pprint import pprint
import json
from datetime import date

with open("PATH/TO/creds.json") as credentials:
    creds = json.load(credentials)

meraki_key = creds['meraki_api']

today = date.today()
meraki_log = open(f"PATH/TO/meraki_log_{today}.txt", "a")

dashboard = meraki.DashboardAPI(
        api_key=meraki_key,
        output_log=False,
        #log_file_prefix=os.path.basename(__file__)[:-3],
        #log_path='',
        print_console=False
    )


def vlan_config(dashboard, network_name, network_id):

    # Enables VLANs and disabled Single LAN settings
    en_vlan_response = dashboard.appliance.updateNetworkApplianceVlansSettings(
        network_id, vlansEnabled=True
    )

    third_octet = input('''
Type the number that the third octet will be using.\n\n
''')

    for number in range(0,4):

        # Deletes the default VLAN that comes onboard.
        if number == 0:
            response = dashboard.appliance.getNetworkApplianceVlans(
                network_id
            )

            for entry in response:
                if "default" in entry['name'].lower():
                    vlan_id = entry['id']
                    remove_default = dashboard.appliance.deleteNetworkApplianceVlan(
                        network_id, vlan_id
                    )
                    meraki_log.write((" " * 8) + 'Deleted the default VLAN\n')
                    pprint('Deleted the default VLAN. Moving on to configuring the site VLANs now...')

        # Configures VLAN 10 under the "Addressing and VLAN" Section
        elif number == 1:
            try:
                id_ = '10'
                vlan_id = '10'
                name = 'USER_DATA'
                subnet = f'192.168.{third_octet}.0/26'
                appliance_ip = f'192.168.{third_octet}.1'

                create_response = dashboard.appliance.createNetworkApplianceVlan(
                    network_id, id_, name, subnet, appliance_ip
                )
                meraki_log.write((" " * 8) + 'VLAN 10 has been created\n')

                # Creates the DHCP options for VLAN 10 under the "DHCP" Section
                dhcp_response = dashboard.appliance.updateNetworkApplianceVlan(
                    network_id, vlan_id,
                    dhcpHandling='Run a DHCP server',
                    dhcpLeaseTime='1 day',
                    dhcpBootOptionsEnabled=False,
                    dnsNameservers='upstream_dns'
                )
                meraki_log.write((" " * 8) + 'VLAN 10 settings have been set\n')
                pprint("Configured VLAN 10 | Internal")

            except:
                print("It appears VLAN 10 already exists.\n")
                print("Moving on\n")
                meraki_log.write((" " * 8) + 'VLAN 10 already exists\n')
                continue

        # Configures VLAN 11 under the "Addressing and VLAN" Section
        elif number == 2:
            try:
                id_ = '11'
                vlan_id = '11'
                name = 'USER_VOICE'
                subnet = f'192.168.{third_octet}.64/27'
                appliance_ip = f'192.168.{third_octet}.65'

                create_response = dashboard.appliance.createNetworkApplianceVlan(
                    network_id, id_, name, subnet, appliance_ip
                )
                meraki_log.write((" " * 8) + 'VLAN 11 has been created\n')

                # Creates the DHCP options for VLAN 10 under the "DHCP" Section
                dhcp_response = dashboard.appliance.updateNetworkApplianceVlan(
                    network_id, vlan_id,
                    dhcpHandling='Run a DHCP server',
                    dhcpLeaseTime='1 day',
                    dhcpBootOptionsEnabled=False,
                    dnsNameservers='upstream_dns'
                )
                meraki_log.write((" " * 8) + 'VLAN 11 settings have been set\n')
                pprint("Configured VLAN 11 | Management")

            except:
                print("It appears VLAN 11 already exists.\n")
                print("Moving on\n")
                meraki_log.write((" " * 8) + 'VLAN 11 already exists\n')
                continue

        # Configures VLAN 11 under the "Addressing and VLAN" Section
        elif number == 3:
            try:
                id_ = '12'
                vlan_id = '12'
                name = 'MANAGEMENT'
                subnet = f'192.168.{third_octet}.96/27'
                appliance_ip = f'192.168.{third_octet}.97'

                create_response = dashboard.appliance.createNetworkApplianceVlan(
                    network_id, id_, name, subnet, appliance_ip
                )
                meraki_log.write((" " * 8) + 'VLAN 12 has been created\n')

                # Creates the DHCP options for VLAN 10 under the "DHCP" Section. In this case, it disables it.
                dhcp_response = dashboard.appliance.updateNetworkApplianceVlan(
                    network_id, vlan_id,
                    dhcpHandling='Do not respond to DHCP requests'
                )
                meraki_log.write((" " * 8) + 'VLAN 12 settings have been set\n')
                pprint("Configured VLAN 12 | iSCSI")

            except:
                print("It appears VLAN 12 already exists.\n")
                print("Moving on\n")
                meraki_log.write((" " * 8) + 'VLAN 12 already exists\n')
                continue

    meraki_log.write((" " * 8) + 'All VLANs have been created\n')
    pprint('All VLANs have been created')

    port_config(dashboard, network_id, third_octet)


def port_config(dashboard, network_id, third_octet):
    print("Configuring per-port VLAN settings")
    for i in range (3, 13):
        port_id = i
        if i == 3 or i == 4:
            print(f"Configuring port: {i}...")
            response = dashboard.appliance.updateNetworkAppliancePort(
                network_id, port_id,
                enabled=True,
                dropUntaggedTraffic=False,
                type='access',
                vlan=10
            )
            meraki_log.write((" " * 8) + f'Port {i} has been configured\n')
            print(f"Finished configuring port: {i} with access settings")

        else:
            print(f"Configuring port: {i}...")
            response = dashboard.appliance.updateNetworkAppliancePort(
                network_id, port_id,
                enabled=True,
                dropUntaggedTraffic=True,
                type='trunk',
                allowedVlans='all'
            )
            meraki_log.write((" " * 8) + f'Port {i} has been configured\n')
            print(f"Finished configuring port: {i} with access settings")
    meraki_log.write((" " * 8) + 'Finished configuring port access settings\n')
    firewall_config(dashboard, network_id, third_octet)


def firewall_config(dashboard, network_id, third_octet):
    # Enables the SNMP setting and restricts it
    print("Configuring SNMP settings now")

    # This section actually configures SNMP to be used.
    snmp_response = dashboard.networks.updateNetworkSnmp(
        network_id,
        access='users',
        users=[{'username': 'SNMPv3_USERNAME', 'passphrase': 'SNMPv3_PASSPHRASE'}]
    )
    meraki_log.write((" " * 8) + 'SNMPv3 was enabled successfully\n')

    # This section configures the FW rules for SNMP
    print('Configuring SNMP firewall settings now')
    service='SNMP'
    access='restricted'

    snmpfw_response = dashboard.appliance.updateNetworkApplianceFirewallFirewalledService(
        network_id, service, access,
        allowedIps=['YOUR_IP_ADDRESSES_HERE]
    )
    meraki_log.write((" " * 8) + 'Firewall rules for SNMP have been created\n')

    # This section configures the forwarding rules on the MX
    print('Configuring firewall port forwarding rules now')
    rules = [
        {
            'lanIp': f'192.168.{third_octet}.1',
            'allowedIps': ['any'],
            'name': 'HTTP',
            'protocol': 'tcp',
            'publicPort': '80',
            'localPort': '80',
            'uplink': 'both'
        },
        {
            'lanIp': f'192.168.{third_octet}.5',
            'allowedIps': ['any'],
            'name': 'HTTPS',
            'protocol': 'tcp',
            'publicPort': '443',
            'localPort': '443',
            'uplink': 'both'
        },
        {
            'lanIp': f'192.168.{third_octet}.5',
            'allowedIps': ['any'],
            'name': 'ODBC',
            'protocol': 'tcp',
            'publicPort': '7771',
            'localPort': '7771',
            'uplink': 'both'
        },
        {
            'lanIp': f'192.168.{third_octet}.5',
            'allowedIps': ['any'],
            'name': 'SSRS',
            'protocol': 'tcp',
            'publicPort': '82',
            'localPort': '82',
            'uplink': 'both'
        }
    ]

    fwconfig_response = dashboard.appliance.updateNetworkApplianceFirewallPortForwardingRules(
        network_id, rules
    )
    meraki_log.write((" " * 8) + 'Firewall settings have been configured\n')
    print('Finished configuring firewall settings.')

    vpn_config(network_id, third_octet)

def vpn_config(network_id, third_octet):
    print('Configuring site-to-site settings now')
    mode = 'spoke'
    vpn_response = dashboard.appliance.updateNetworkApplianceVpnSiteToSiteVpn(
        network_id, mode,
        hubs=[{
            "hubId": 'YOUR_HUB_ID_HERE', 'useDefaultRoute': False
        }],
        subnets=[
            {'localSubnet': f'192.168.{third_octet}.0/26', 'useVpn': True},
            {'localSubnet': f'192.168.{third_octet}.64/27', 'useVpn': True},
            {'localSubnet': f'192.168.{third_octet}.96/27', 'useVpn': False}
        ]
    )
    meraki_log.write((" " * 8) + f'Site-to-site VPN settings have been configured using mode: {mode}\n')

    # This section defines the VPN-specific rules for site-to-site outbound traffic
    print('Creating site-to-site VPN forwarding rules now')
    rules = [
        {
            "policy": "deny",
            "protocol": "any",
            "srcCidr": "SOURCE_HERE",
            "srcPort": "any",
            "destCidr": "DESTINATION_HERE",
            "destPort": "any",
            "comment": "COMMENT_HERE",
            "syslogEnabled": True
        },
        {
            "policy": "allow",
            "protocol": "any",
            "srcCidr": "SOURCE_HERE",
            "srcPort": "any",
            "destCidr": "DESTINATION_HERE",
            "destPort": "any",
            "comment": "COMMENT_HERE",
            "syslogEnabled": True
        },
        {
            "policy": "deny",
            "protocol": "any",
            "srcCidr": "SOURCE_HERE",
            "srcPort": "any",
            "destCidr": "DESTINATION_HERE",
            "destPort": "any",
            "comment": "COMMENT_HERE",
            "syslogEnabled": True
        },
        {
            "policy": "allow",
            "protocol": "any",
            "srcCidr": "SOURCE_HERE",
            "srcPort": "any",
            "destCidr": "DESTINATION_HERE",
            "destPort": "any",
            "comment": "COMMENT_HERE",
            "syslogEnabled": True
        }
    ]
    meraki_log.write((" " * 8) + 'Site-to-site ACLs have been configured\n\n')

def network_creation(dashboard, serial_number, organization_id):

    network_name = input('''
Type the name of the network.\n\n
''')


    verify = input(f'''
You've typed: {network_name}. Is this correct? Y/n    
''')

    if "Y" in verify or "y" in verify.lower():
        time_choice = input('''
Type the number corresponding to the time zone the network will exist in:
1. America/New York (Eastern)
2. America/Chicago (Central)
3. America/Denver (Mountain)
4. America/Los Angeles (Pacific)\n\n
''')
        if "1" in time_choice:
            product_types = ["appliance"]
            name = network_name
            try:
                print(f'Please wait, creating network: {network_name} now...')
                create_net_response = dashboard.organizations.createOrganizationNetwork(
                    organization_id, name, product_types,
                    timeZone='America/New York'
                )

                get_net_response = dashboard.organizations.getOrganizationNetworks(
                    organization_id, total_pages='all'
                )
                meraki_log.write(f'{network_name} has been created in timezone: America/New York\n')

                for entry in get_net_response:
                    if name in entry['name']:
                        # pprint(entry['name'])
                        # pprint(entry['id'])
                        network_id = entry['id']

                        print(f'{name} has been successfully created. Binding open MX84 to network now... ')
                        serials = [f'{serial_number}']
                        bind_device = dashboard.networks.claimNetworkDevices(
                            network_id, serials
                        )
                        meraki_log.write((" " * 8) + f'Serial number: {serial_number} is now bound to {network_name}\n')

                        print(f'Successfully bound MX84 with serial #: {serial_number} to network: {name}')
                        vlan_config(dashboard, network_name, network_id)
            except:
                print('This network name is already in use. Please verify name and try again')
                network_creation(dashboard, serial_number, organization_id)

        elif "2" in time_choice:
            product_types = ["appliance"]
            name = network_name
            try:
                print(f'Please wait, creating network: {network_name} now...')
                create_net_response = dashboard.organizations.createOrganizationNetwork(
                    organization_id, name, product_types,
                    timeZone='America/Chicago'
                )
                meraki_log.write(f'{network_name} has been created in timezone: America/Chicago\n')

                get_net_response = dashboard.organizations.getOrganizationNetworks(
                    organization_id, total_pages='all'
                )

                for entry in get_net_response:
                    if name in entry['name']:
                        # pprint(entry['name'])
                        # pprint(entry['id'])
                        network_id = entry['id']

                        print(f'{name} has been successfully created. Binding open MX84 to network now...')
                        serials = [f'{serial_number}']
                        bind_device = dashboard.networks.claimNetworkDevices(
                            network_id, serials
                        )
                        meraki_log.write((" " * 8) + f'Serial number: {serial_number} is now bound to {network_name}\n')

                        print(f'Successfully bound MX84 with serial #: {serial_number} to network: {name}')
                        vlan_config(dashboard, network_name, network_id)
            except:
                print('This network name is already in use. Please verify name and try again')
                network_creation(dashboard, serial_number, organization_id)

        elif "3" in time_choice:
            product_types = ["appliance"]
            name = network_name
            try:
                print(f'Please wait, creating network: {network_name} now...')
                create_net_response = dashboard.organizations.createOrganizationNetwork(
                    organization_id, name, product_types,
                    timeZone='America/Denver'
                )
                meraki_log.write(f'{network_name} has been created in timezone: America/Denver\n')

                get_net_response = dashboard.organizations.getOrganizationNetworks(
                    organization_id, total_pages='all'
                )

                for entry in get_net_response:
                    if name in entry['name']:
                        # pprint(entry['name'])
                        # pprint(entry['id'])
                        network_id = entry['id']

                        print(f'{name} has been successfully created. Binding open MX84 to network now...')
                        serials = [f'{serial_number}']
                        bind_device = dashboard.networks.claimNetworkDevices(
                            network_id, serials
                        )
                        meraki_log.write((" " * 8) + f'Serial number: {serial_number} is now bound to {network_name}\n')

                        print(f'Successfully bound MX84 with serial #: {serial_number} to network: {name}')
                        vlan_config(dashboard, network_name, network_id)
            except:
                print('This network name is already in use. Please verify name and try again')
                network_creation(dashboard, serial_number, organization_id)

        elif "4" in time_choice:
            product_types = ["appliance"]
            name = network_name
            try:
                print(f'Please wait, creating network: {network_name} now...')
                create_net_response = dashboard.organizations.createOrganizationNetwork(
                    organization_id, name, product_types,
                    timeZone='America/Los Angeles'
                )
                meraki_log.write(f'{network_name} has been created in timezone: America/Los Angeles\n')

                get_net_response = dashboard.organizations.getOrganizationNetworks(
                    organization_id, total_pages='all'
                )

                for entry in get_net_response:
                    if name in entry['name']:
                        # pprint(entry['name'])
                        # pprint(entry['id'])
                        network_id = entry['id']

                        print(f'{name} has been successfully created. Binding open MX84 to network now...')
                        serials = [f'{serial_number}']
                        bind_device = dashboard.networks.claimNetworkDevices(
                            network_id, serials
                        )
                        meraki_log.write((" " * 8) + f'Serial number: {serial_number} is now bound to {network_name}\n')

                        print(f'Successfully bound MX84 with serial #: {serial_number} to network: {name}')
                        vlan_config(dashboard, network_name, network_id)
            except:
                meraki_log.write(f'Network name: {network_name} has already been taken. Asking user to re-attempt\n')
                print('This network name is already in use. Please verify name and try again')
                network_creation(dashboard, serial_number, organization_id)

    else:
        network_creation(dashboard, serial_number, organization_id)


def main(dashboard):
    print('Please wait, gathering organization information \n')
    org_id_list = []
    organizations = dashboard.organizations.getOrganizations()

    open_device_list = []
    for org in organizations:
        organization_id = org['id']
        org_id_list.append(org['id'])

        open_devices = dashboard.organizations.getOrganizationInventoryDevices(
            organization_id, total_pages='all'
        )

        for entry in open_devices:
            if entry['model'] == 'MX84' and entry['networkId'] is None:
                open_device_list.append(entry['serial'])

    serial_number = open_device_list[0]

    organization_id = org_id_list[0]
    network_creation(dashboard, serial_number, organization_id)


if __name__ == "__main__":
    main(dashboard)