#every command must end with a new line (\n) so a complete script can be build
chipset_methods = {}
chipset_methods['wl'] = "{command} -i {interfaces} assoclist\n"
chipset_methods['iwinfo'] = "{command} {interfaces} assoclist\n"
chipset_methods['wlanconfig'] = "{command} {interfaces} list\n"
chipset_methods['wl_atheros'] = "{command} -i {interfaces} assoclist\n"
chipset_methods['qcsapi_sockrpc'] = "concount=$({command} get_count_assoc {interfaces});i=0;while [[ $i -lt $concount ]]; do {command} get_station_mac_addr {interfaces} $i;i=$((i+1));done\n"
generic_methods= {}
generic_methods['ip'] = "{command} neighbour\n"
generic_methods['brctl'] = "{command} showmacs br0\n"
generic_methods['arp'] = "{command} -a\n"
generic_methods['cat'] = "{command} /proc/net/arp\n"
generic_method_order = ['ip', 'brctl', 'arp', 'cat']

command_wrapper = '{part}exit'

interface_check={}
interface_check['wl']="""
for iface in $(ifconfig | cut -d ' ' -f1| tr ':' '\n' | grep -E '^eth|^wlan|^wl');do
	{command} -i $iface assoclist > /dev/null 2>&1 && printf "~$iface"
done
"""
interface_check['iwinfo']="""
for iface in $(ifconfig | cut -d ' ' -f1| tr ':' '\n' | grep -E '^eth|^wlan|^ath|^wl');do
	{command} $iface assoclist > /dev/null 2>&1 && printf "~$iface"
done
"""

interface_check['wlanconfig']="""
for iface in $(ifconfig | cut -d ' ' -f1| tr ':' '\n' | grep -E '^eth|^wlan|^ath|^wl');do
	testif=`wlanconfig $iface list 2>&1`
	[ $? == 0 ] && [ "$testif" != "Not supported" ] && printf "~$iface"
done
"""

interface_check['wl_atheros']="""
for iface in $(ifconfig | cut -d ' ' -f1| tr ':' '\n' | grep -E '^eth|^wlan|^ath|^wl');do
	{command} -i $iface assoclist > /dev/null 2>&1 && printf "~$iface"
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
type wl_atheros
type qcsapi_sockrpc
type ip
type brctl
type arp
[ -f /proc/net/arp ] && type cat
echo 0
"""

import DomoticzEx

def get_try_available_commands_cli():
	functional_part = try_available_commands
	full_command = wrap_command(functional_part)
	return full_command

def get_try_interface_cli(chipset, command_path):
	if chipset in interface_check:
		functional_part = interface_check[chipset].format(command=command_path)
		full_command = wrap_command(functional_part)
	return full_command

def get_tracker_cli(command_id, command_path, command_interfaces=''):
	if command_id in chipset_methods:
		full_command = chipset_methods[command_id].format(command=command_path, interfaces=command_interfaces)
	elif command_id in generic_methods:
		full_command = generic_methods[command_id].format(command=command_path)
	else:
		full_command = ''
	return full_command

def wrap_command(functional):
	full_command = command_wrapper.format(part=functional)
	return full_command
