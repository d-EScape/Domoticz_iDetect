
chipset_methods = {}
chipset_methods['wl'] = "{command} -i {interfaces} assoclist"
chipset_methods['iwinfo'] = "{command} {interfaces} assoclist"
chipset_methods['wlanconfig'] = "{command} {interfaces} list"
chipset_methods['qcsapi_sockrpc'] = "concount=$({command} get_count_assoc {interfaces});i=0;while [[ $i -lt $concount ]]; do {command} get_station_mac_addr {interfaces} $i;i=$((i+1));done"
generic_methods= {}
generic_methods['ip'] = "{command} neighbour"
generic_methods['brctl'] = "{command} showmacs br0"
generic_methods['arp'] = "{command} -a"
generic_methods['cat'] = "{command} /proc/net/arp"
generic_method_order = ['ip', 'brctl', 'arp', 'cat']

interface_check={}
interface_check['wl']="""
for iface in $(ifconfig | cut -d ' ' -f1| tr ':' '\n' | grep -E '^eth|^wlan');do
	{command} -i $iface assoclist > /dev/null 2>&1 && printf "~$iface"
done
"""
interface_check['iwinfo']="""
for iface in $(ifconfig | cut -d ' ' -f1| tr ':' '\n' | grep -E '^eth|^wlan|^ath');do
	{command} $iface assoclist > /dev/null 2>&1 && printf "~$iface"
done
"""

interface_check['wlanconfig']="""
for iface in $(ifconfig | cut -d ' ' -f1| tr ':' '\n' | grep -E '^eth|^wlan|^ath');do
	{command} $iface list > /dev/null 2>&1 && printf "~$iface"
done
"""

interface_check['qcsapi_sockrpc']="""
for iface in $(qcsapi_sockrpc get_primary_interface);do
	{command} get_assoc_records $iface > /dev/null 2>&1 && printf "~$iface"
done
"""

try_available_commands="""
export PATH=/usr/sbin:/usr/bin:/usr/local/sbin:/usr/local/bin:/sbin:/bin:$PATH
type wl
type iwinfo
type wlanconfig
type qcsapi_sockrpc
type ip
type brctl
type arp
[ -f /proc/net/arp ] && type cat
echo 0
"""

import Domoticz

def get_try_available_commands_cli():
	full_command = try_available_commands
#	full_command = wrap_command(functional_part)
	return full_command

def get_try_interface_cli(chipset, command_path):
	if chipset in interface_check:
		full_command = interface_check[chipset].format(command=command_path)
	return full_command
	
def get_tracker_cli(command_id, command_path, command_interfaces=''):
	if command_id in chipset_methods:
		full_command = chipset_methods[command_id].format(command=command_path, interfaces=command_interfaces)
	elif command_id in generic_methods:
		full_command = generic_methods[command_id].format(command=command_path)
	else:
		full_command = ''
	return full_command