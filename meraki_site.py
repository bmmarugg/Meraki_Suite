import meraki
from pprint import pprint
import json
from datetime import date, datetime
import requests
import urllib3

urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

with open("PATH/TO/creds.json") as credentials:
    creds = json.load(credentials)

meraki_key = creds['meraki_api']
ib_user = creds['ib_admin_user']
ib_pass = creds['ib_admin_pass']

ib_url = "YOUR.INFOBLOX.URL"


class MerakiSite:
    def __init__(self, site_name, time_zone, host_size, third_octet):
        self.site_name = site_name  # Expects String
        self.time_zone = time_zone
        self.host_size = host_size # expects a string of an integer. In this case, either "2" or "3"
        self.third_octet = third_octet

    ### Gets the dashboard information using the API key supplied in creds.json
    dashboard = meraki.DashboardAPI(
        api_key=meraki_key,
        output_log=False,
        print_console=False
    )

    ### Now it gets the organization ID(s) from the dashboard information
    org_id_list = []
    organizations = dashboard.organizations.getOrganizations()

    for org in organizations:
        organization_id = org['id']
        org_id_list.append(org['id'])

    organization_id = org_id_list[0]


    ### Creates the new network/site using the user-input parameters
    def create_network(self):

        product_types = ['appliance']
        name = self.site_name
        print(f'Please wait, configuring network: {self.site_name}')

        self.dashboard.organizations.createOrganizationNetwork(
            self.organization_id, name, product_types,
            timeZone=self.time_zone
        )


    ### Finds the first open MX84 and binds it to the network.
    ### You can change the device type my editing line 67 to edit the model string the script looks for.
    def bind_device(self):
        open_device_list = []
        open_devices = self.dashboard.organizations.getOrganizationInventoryDevices(
            self.organization_id, total_pages='all'
        )

        for entry in open_devices:
            if entry['model'] == 'MX84' and entry['networkId'] is None:
                open_device_list.append(entry['serial'])

        bind_choice = input("""
Type the number corresponding to how the device will be bound:
1) Automatic
2) Manual        
""")

        if "2" in bind_choice or "manual" in bind_choice.lower():
            for entry in open_device_list:
                pprint(entry)

            user_dev_choice = input("""
Type the serial number of the device you want to bind EXACTLY as it appears above:
""")

            serials = [f'{user_dev_choice}']
            get_net_response = self.dashboard.organizations.getOrganizationNetworks(
                self.organization_id, total_pages='all'
            )

            for entry in get_net_response:
                if self.site_name in entry['name']:
                    network_id = entry['id']
                    self.dashboard.networks.claimNetworkDevices(
                        network_id, serials
                    )
                    pprint(f"Successfully bound device with serial number: {user_dev_choice}")

                    ### Configures device name as a part of this process
                    device_name = self.site_name.split(" ")
                    device_name = 'd' + device_name[0] + device_name[-1] + '-fw1'
                    print('Configuring device name now')

                    # "serial" is different than "serials"
                    serial = f'{user_dev_choice}'
                    self.dashboard.devices.updateDevice(
                        serial,
                        name=f'{device_name.lower()}'
                    )

        else:
            for entry in open_devices:
                if entry['model'] == 'MX84' and entry['networkId'] is None:
                    open_device_list.append(entry['serial'])
            serial_number = open_device_list[0]
            serials = [f'{serial_number}']
            get_net_response = self.dashboard.organizations.getOrganizationNetworks(
                self.organization_id, total_pages='all'
            )

            for entry in get_net_response:
                if self.site_name in entry['name']:
                    network_id = entry['id']
                    self.dashboard.networks.claimNetworkDevices(
                        network_id, serials
                    )
                    pprint(f"Successfully bound device with serial number: {serial_number}")

                    ### Configures device name as a part of this process
                    device_name = self.site_name.split(" ")
                    device_name = 'd' + device_name[0] + device_name[-1] + '-fw1'
                    print('Configuring device name now')

                    # "serial" is different than "serials"
                    serial = f'{serial_number}'
                    self.dashboard.devices.updateDevice(
                        serial,
                        name=f'{device_name.lower()}'
                    )

    ### Gets the serial number without re-running the script that binds a device to the newly created network
    def get_serial_number(self):
        network_id = new_meraki_site.get_net_id()

        response = self.dashboard.networks.getNetworkDevices(
            network_id
        )

        for entry in response:
            bound_serial_number = entry['serial']
            return bound_serial_number


    ### Gets the unique network ID value of the network we just created
    def get_net_id(self):
        org_id_list = []
        organizations = self.dashboard.organizations.getOrganizations()

        for org in organizations:
            org_id_list.append(org['id'])

        organization_id = org_id_list[0]

        get_net_response = self.dashboard.organizations.getOrganizationNetworks(
            organization_id, total_pages='all'
        )
        for entry in get_net_response:
            if self.site_name in entry['name']:
                network_id = entry['id']
                return network_id


    ### Enables VLANs instead of the default single LAN and removes the default VLAN
    def enable_vlan(self):
        network_id = new_meraki_site.get_net_id()

        # Enables VLANs
        self.dashboard.appliance.updateNetworkApplianceVlansSettings(
            network_id, vlansEnabled=True
        )

        # Deletes the default VLAN
        default_vlan_response = self.dashboard.appliance.getNetworkApplianceVlans(
                network_id
            )

        for entry in default_vlan_response:
            if "default" in entry['name'].lower():
                vlan_id = entry['id']
                self.dashboard.appliance.deleteNetworkApplianceVlan(
                    network_id, vlan_id
                )


    ### Actually creates the VLANs now and configures them with IP information pulled from InfoBlox. You will be
    ### Responsible for changing the IP address information, VLAN IDs, default gateways, etc. These are examples.
    def create_vlans(self):
        network_id = new_meraki_site.get_net_id()

        for i in range (0, 3):
            if i == 0:
                id_ = '10'
                vlan_id = '10'
                name = 'EXAMPLE_1'
                subnet = f'10.10.{self.third_octet}.0/26'
                appliance_ip = f'10.10.{self.third_octet}.1'

                self.dashboard.appliance.createNetworkApplianceVlan(
                    network_id, id_, name, subnet, appliance_ip
                )

                # Creates the DHCP options for VLAN 10 under the "DHCP" Section
                self.dashboard.appliance.updateNetworkApplianceVlan(
                    network_id, vlan_id,
                    dhcpHandling='Run a DHCP server',
                    dhcpLeaseTime='1 day',
                    dhcpBootOptionsEnabled=False,
                    dnsNameservers='upstream_dns'
                )

            elif i == 1:
                id_ = '11'
                vlan_id = '11'
                name = 'EXAMPLE_2'
                subnet = f'10.10.{third_octet}.64/27'
                appliance_ip = f'10.10.{third_octet}.65'

                self.dashboard.appliance.createNetworkApplianceVlan(
                    network_id, id_, name, subnet, appliance_ip
                )

                # Creates the DHCP options for VLAN 11 under the "DHCP" Section
                self.dashboard.appliance.updateNetworkApplianceVlan(
                    network_id, vlan_id,
                    dhcpHandling='Run a DHCP server',
                    dhcpLeaseTime='1 day',
                    dhcpBootOptionsEnabled=False,
                    dnsNameservers='upstream_dns'
                )

            elif i == 2:
                id_ = '12'
                vlan_id = '12'
                name = 'EXAMPLE_3'
                subnet = f'10.10.{self.third_octet}.96/27'
                appliance_ip = f'10.10.{self.third_octet}.97'

                self.dashboard.appliance.createNetworkApplianceVlan(
                    network_id, id_, name, subnet, appliance_ip
                )

                # Creates the DHCP options for VLAN 12 under the "DHCP" Section. In this case, it disables it.
                self.dashboard.appliance.updateNetworkApplianceVlan(
                    network_id, vlan_id,
                    dhcpHandling='Do not respond to DHCP requests'
                )


    ### Configures the per-port settings on the MX-84 itself. If you choose a different model type to assign to the
    ### network, you'll need to change the port numbers. These are just examples for what the code will look like for
    ### configuring ports 3 and 4, depending on the number of hosts that will be connected to the Meraki device.
    def port_config(self):
        network_id = new_meraki_site.get_net_id()

        if self.host_size == "1":
            for i in range(3, 13):
                port_id = i
                if i == 3:
                    print(f"Configuring port: {i}...")
                    self.dashboard.appliance.updateNetworkAppliancePort(
                        network_id, port_id,
                        enabled=True,
                        dropUntaggedTraffic=False,
                        type='access',
                        vlan=10
                    )
                    print(f"Finished configuring port: {i} with access settings")

                else:
                    print(f"Configuring port: {i}...")
                    self.dashboard.appliance.updateNetworkAppliancePort(
                        network_id, port_id,
                        enabled=True,
                        dropUntaggedTraffic=True,
                        type='trunk',
                        allowedVlans='all'
                    )
                    print(f"Finished configuring port: {i} with access settings")

        elif self.host_size == "2":
            for i in range(3, 13):
                port_id = i
                if i == 3 or i == 4:
                    print(f"Configuring port: {i}...")
                    self.dashboard.appliance.updateNetworkAppliancePort(
                        network_id, port_id,
                        enabled=True,
                        dropUntaggedTraffic=False,
                        type='access',
                        vlan=10
                    )
                    print(f"Finished configuring port: {i} with access settings")

                else:
                    print(f"Configuring port: {i}...")
                    self.dashboard.appliance.updateNetworkAppliancePort(
                        network_id, port_id,
                        enabled=True,
                        dropUntaggedTraffic=True,
                        type='trunk',
                        allowedVlans='all'
                    )
                    print(f"Finished configuring port: {i} with access settings")


    ### Configures SNMP related settings. You will need to provide your own SNMPv3 username and passphrase (line 286),
    ### in addition to your SNMP server IP address (line 296)
    def snmp_config(self):
        network_id = new_meraki_site.get_net_id()

        # Enables the SNMP setting and restricts it
        print("Configuring SNMP settings now")

        # This section actually configures SNMP to be used.
        self.dashboard.networks.updateNetworkSnmp(
            network_id,
            access='users',
            users=[{'username': 'SNMPv3_USER_HERE', 'passphrase': 'SNMPv3_PASSPHRASE_HERE'}]
        )

        # This section configures the FW rules for SNMP
        print('Configuring SNMP firewall settings now')
        service = 'SNMP'
        access = 'restricted'

        self.dashboard.appliance.updateNetworkApplianceFirewallFirewalledService(
            network_id, service, access,
            allowedIps=['ALLOWED_IP_HERE']
        )


    ### Configures firewall and firewall-related settings. These are just example rules to show format and the necessary
    ### Meraki key-value pairs.
    def firewall_config(self):
        network_id = new_meraki_site.get_net_id()

        print('Configuring firewall port forwarding rules now')
        rules = [
            {
                'lanIp': f'10.10.{self.third_octet}.1',
                'allowedIps': ['any'],
                'name': 'HTTP',
                'protocol': 'tcp',
                'publicPort': '80',
                'localPort': '80',
                'uplink': 'both'
            },
            {
                'lanIp': f'10.10.{self.third_octet}.1',
                'allowedIps': ['any'],
                'name': 'HTTPS',
                'protocol': 'tcp',
                'publicPort': '443',
                'localPort': '443',
                'uplink': 'both'
            }
        ]

        self.dashboard.appliance.updateNetworkApplianceFirewallPortForwardingRules(
            network_id, rules
        )


    ### Configures the VPN security settings to allow specific subnets out the VPN. You will need to provide the ID of
    ### Your organization's hub in line 343.
    def vpn_config(self):
        network_id = new_meraki_site.get_net_id()

        # Configures the spoke-specific rules for the VPN
        print('Configuring site-to-site settings now')
        mode = 'spoke'
        self.dashboard.appliance.updateNetworkApplianceVpnSiteToSiteVpn(
            network_id, mode,
            hubs=[{
                "hubId": 'HUB_ID_HERE', 'useDefaultRoute': False
            }],
            ### Allows the site-specific third-octet out the VPN
            subnets=[
                {'localSubnet': f'10.10.{self.third_octet}.0/26', 'useVpn': True},
                {'localSubnet': f'10.10.{self.third_octet}.96/27', 'useVpn': False}
            ]
        )


    ### Creates a Microsoft Teams posting to the Network Automation Notifications space with details. You'll need to
    ### provide your own Teams room URL in line 369.
    def teams_posting(self):
        bound_serial_number = new_meraki_site.get_serial_number()

        headers = {
            'Content-Type': "application/json",
            'Accept': "*/*",
            'Cache-Control': "no-cache",
            'Host': "outlook.office.com",
            'accept-encoding': "gzip, deflate",
            'content-length': "1613",
            'Connection': "keep-alive",
            'cache-control': "no-cache"
        }

        url = "TEAMS_ROOM_URL_HERE"

        payload = '''  
        	{
        		"@type": "MessageCard",
        		"@context": "https://schema.org/extensions",
        		"themeColor": "7471D8",
        		"sections": [
        			{
        				"activityTitle": "Meraki Script Notification",
        				"activitySubtitle": "New site has been created with the following details:",
        				"facts": [
        				    {
        					    "name": "Script execution time",
        					    "value": "''' + datetime.now().strftime("%H:%M:%S") + '''"
        					},
        					{
        						"name": "Script Name",
        						"value": "Meraki Site Configuration"
        					},
        					{
        					    "name": "New Site Created",
        					    "value": "''' + self.site_name + '''"
        					},
        					{
        					    "name": "Meraki SN",
        					    "value": "''' + bound_serial_number + '''"
        					},
        					{
        					    "name": "Selected Host Size",
        					    "value": "''' + self.host_size + '''"
        					},
        					{
        					    "name": "Configured third octet (/24)",
        					    "value": "''' + f'10.10.{self.third_octet}.0' + '''"
        					}
        				]
        			}
        		]
        	}'''

        requests.request("POST", url, data=payload, headers=headers)


### User-defined site name
def user_site_name():
    site_name = input("Type the name of the site: ")
    return site_name


### User-defined time-zone. This is what the newly created network will use for its Timezone. Just type the integer
### corresponding to the appropriate time-zone. Eg. "1" for Eastern, "2" for Central, etc.
def user_time_choice():
    time_choice = input('''\n
Type the number corresponding to the time zone the network will exist in:
1. America/New York (Eastern)
2. America/Chicago (Central)
3. America/Denver (Mountain)
4. America/Los Angeles (Pacific)\n\n
''')

    if "1" in time_choice:
        time_zone = "America/New_York"
        return time_zone
    elif "2" in time_choice:
        time_zone = "America/Chicago"
        return time_zone
    elif "3" in time_choice:
        time_zone = "America/Denver"
        return time_zone
    elif "4" in time_choice:
        time_zone = "America/Los_Angeles"
        return time_zone
    else:
        print("Invalid time zone selection detected. Please enter a valid integer for the time zone.\n")
        user_time_choice()


### User-defined number of hosts at the district. This is important because it affects the port configuration settings
def get_host_size():
    user_host_size = input('''
\nPlease type the number of Nutanix hosts that will be deployed in-district. Acceptable values as of right now are "1" through 
"3" \n    
''')
    if "1" in user_host_size:
        host_size = "1"
        return host_size
    elif "2" in user_host_size:
        host_size = "2"
        return host_size
    elif "3" in user_host_size:
        host_size = "3"
        return host_size
    else:
        print('''
Invalid selection detected. Please type either "2" or "3". If the district has more hosts, submit a ticket with Network
''')
        get_host_size()


### Uses InfoBlox to get the next available /24 from 10.64.0.0/16 and uses this third octet for all IP changes. You'll
### need to provide your own URL for all the lines with "YOUR_INFOBLOX_URL_HERE"
def get_third_octet():
    payload = {
        "network": "func:nextavailablenetwork:10.64.0.0/16,default,24",
        "network_view": "default",
        "comment": f"{site_name}"
    }
    response = requests.post(
        "https://YOUR_INFOBLOX_URL_HERE/wapi/v2.10.5/network?_return_fields%2B=network_container,members,extattrs&_return_as_object=1",
        auth=(ib_user, ib_pass), verify=False, data=json.dumps(payload))

    #pprint(response.json())

    network_info = {}
    network_info['net_id'] = response.json()['result']['_ref']
    network_info['subnet'] = response.json()['result']['network']
    ib_net_info = network_info['subnet']

    third_octet = network_info['subnet'].split(".")[-2]

    sub1_payload = {
        "network": f"func:nextavailablenetwork:{ib_net_info},default,26",
        "network_view": "default",
        "comment": f"{site_name}  EXAMPLE_1"
    }
    requests.post(
        "https://iYOUR_INFOBLOX_URL_HERE/wapi/v2.10.5/network?_return_fields%2B=network,members,extattrs&_return_as_object=1",
        auth=(ib_user, ib_pass), verify=False, data=json.dumps(sub1_payload))

    sub2_payload = {
        "network": f"func:nextavailablenetwork:{ib_net_info},default,27",
        "network_view": "default",
        "comment": f"{site_name}  EXAMPLE_2"
    }
    requests.post(
        "https://YOUR_INFOBLOX_URL_HERE/wapi/v2.10.5/network?_return_fields%2B=network,members,extattrs&_return_as_object=1",
        auth=(ib_user, ib_pass), verify=False, data=json.dumps(sub2_payload))

    sub3_payload = {
        "network": f"func:nextavailablenetwork:{ib_net_info},default,27",
        "network_view": "default",
        "comment": f"{site_name}  EXAMPLE_3"
    }
    requests.post(
        "https://YOUR_INFOBLOX_URL_HERE/wapi/v2.10.5/network?_return_fields%2B=network,members,extattrs&_return_as_object=1",
        auth=(ib_user, ib_pass), verify=False, data=json.dumps(sub3_payload))

    return third_octet


### Function calls to kick off the script
site_name = user_site_name()
time_zone = user_time_choice()
host_size = get_host_size()
third_octet= get_third_octet()


new_meraki_site = MerakiSite(site_name, time_zone, host_size, third_octet)
new_meraki_site.create_network()
new_meraki_site.bind_device()
new_meraki_site.enable_vlan()
new_meraki_site.create_vlans()
new_meraki_site.port_config()
new_meraki_site.snmp_config()
new_meraki_site.firewall_config()
new_meraki_site.vpn_config()
new_meraki_site.teams_posting()

