
chipset_methods = {}
chipset_methods['wl'] = "wl -i {interfaces} assoclist | cut -d' ' -f2"
chipset_methods['iwinfo'] = "iwinfo {interfaces} assoclist | grep '^..:..:..:..:..:.. ' | cut -d' ' -f1"
chipset_methods['wlanconfig'] = "wlanconfig {interfaces} list | grep '^..:..:..:..:..:.. ' | cut -d' ' -f1"
chipset_methods['qcsapi_sockrpc'] = "concount=$(qcsapi_sockrpc get_count_assoc {interfaces});i=0;while [[ $i -lt $concount ]]; do qcsapi_sockrpc get_station_mac_addr {interfaces} $i;i=$((i+1));done"
generic_methods={}
generic_methods['brctl']="brctl showmacs br0 | grep '..:..:..:..:..:..' | awk '{print $ 2}'"
generic_methods['arp']="arp -a | grep '..:..:..:..:..:..' | awk '{print $ 4}'"
generic_methods['procarp']="cat /proc/net/arp | grep '..:..:..:..:..:..' | awk '{print $ 4}'"

linux_wrapper = "export PATH=/usr/sbin:/usr/bin:/usr/local/sbin:/usr/local/bin:/sbin:/bin:$PATH\n{pollcommand}\nexit"

interface_check={}
interface_check['wl']="""
for iface in $(ifconfig | cut -d ' ' -f1| tr ':' '\n' | grep -E '^eth|^wlan');do
	wl -i $iface assoclist > /dev/null 2>&1 && printf "~$iface"
done
"""
interface_check['iwinfo']="""
for iface in $(ifconfig | cut -d ' ' -f1| tr ':' '\n' | grep -E '^eth|^wlan|^ath');do
	iwinfo $iface assoclist > /dev/null 2>&1 && printf "~$iface"
done
"""

interface_check['wlanconfig']="""
for iface in $(ifconfig | cut -d ' ' -f1| tr ':' '\n' | grep -E '^eth|^wlan|^ath');do
	wlanconfig $iface list > /dev/null 2>&1 && printf "~$iface"
done
"""

interface_check['qcsapi_sockrpc']="""
for iface in $(qcsapi_sockrpc get_primary_interface);do
	qcsapi_sockrpc get_assoc_records $iface > /dev/null 2>&1 && printf "~$iface"
done
"""

try_available_commands="""
type wl > /dev/null 2>&1 && printf "~wl"
type iwinfo > /dev/null 2>&1 && printf "~iwinfo"
type wlanconfig > /dev/null 2>&1 && printf "~wlanconfig"
type qcsapi_sockrpc > /dev/null 2>&1 && printf "~qcsapi_sockrpc"
type brctl > /dev/null 2>&1 && printf "~brctl"
type arp > /dev/null 2>&1 && printf "~arp"
[ -f /proc/net/arp ] && printf "~procarp"
printf "~endoflist"
"""

def get_try_available_commands_cli():
	functional_part = try_available_commands
	full_command = wrap_command(functional_part)
	return full_command

def get_try_interface_cli(chipset):
	if chipset in interface_check:
		functional_part = interface_check[chipset]
		full_command = wrap_command(functional_part)
	return full_command
	
def get_tracker_cli(command, supported_interfaces):
	if command in chipset_methods:
		full_command = chipset_methods[command].format(interfaces=supported_interfaces)
	elif command in generic_methods:
		full_command = generic_methods[command]
	else:
		full_command = ''
	return full_command
	
def wrap_command(functional_command):
	wrapped_command = linux_wrapper.format(pollcommand=functional_command)
	return wrapped_command		