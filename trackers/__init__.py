import Domoticz

from trackers.ping_tracker import ping_tracker
from trackers.fake_tracker import fake_tracker
try:
	from trackers.ssh_tracker import ssh_tracker
	from trackers.ssh_autodetect import ssh_autodetect
	from trackers.ssh_autodetect_generic import ssh_autodetect_generic
	from trackers.ssh_brctl import ssh_brctl
	from trackers.ssh_routeros import ssh_routeros
	from trackers.ssh_routeros_capsman import ssh_routeros_capsman
	from trackers.ssh_routeros_arp import ssh_routeros_arp
	from trackers.ssh_zyxel_arp import ssh_zyxel_arp
	from trackers.ssh_unifi_usg_arp import ssh_unifi_usg_arp
	from trackers.ssh_aimesh_json import ssh_aimesh_json
except ModuleNotFoundError:
	Domoticz.Debug("Required modules for ssh tracker are not installed")
	from trackers.unavailable_tracker import unavailable_tracker as ssh_tracker
	from trackers.unavailable_tracker import unavailable_tracker as ssh_autodetect
	from trackers.unavailable_tracker import unavailable_tracker as ssh_autodetect_generic
	from trackers.unavailable_tracker import unavailable_tracker as ssh_brctl
	from trackers.unavailable_tracker import unavailable_tracker as ssh_routeros
	from trackers.unavailable_tracker import unavailable_tracker as ssh_routeros_capsman
	from trackers.unavailable_tracker import unavailable_tracker as ssh_routeros_arp
	from trackers.unavailable_tracker import unavailable_tracker as ssh_zyxel_arp
	from trackers.unavailable_tracker import unavailable_tracker as ssh_zyxel_arp
	from trackers.unavailable_tracker import unavailable_tracker as ssh_unifi_usg_arp
	from trackers.unavailable_tracker import unavailable_tracker as ssh_aimesh_json
	
from trackers.http_orbi import http_orbi
from trackers.http_unifi import http_unifi
from trackers.http_omada import http_omada
try:
	from trackers.fritzbox import fritzbox
except ModuleNotFoundError:
	Domoticz.Debug("Required modules for fritzbox tracker are not installed")
	from trackers.unavailable_tracker import unavailable_tracker as fritzbox
try:
	from trackers.soap_netgear import soap_netgear
except ModuleNotFoundError:
	Domoticz.Debug("Required modules for netgear-soap tracker are not installed")
	from trackers.unavailable_tracker import unavailable_tracker as soap_netgear
try:
	from trackers.test_error_tracker import test_error_tracker
except ModuleNotFoundError:
	Domoticz.Debug("Required modules for test_error_tracker tracker are not installed")
	from trackers.unavailable_tracker import unavailable_tracker as test_error_tracker	
	
	
	
poll_methods = {
    'default': ssh_autodetect,
    'forcegeneric': ssh_autodetect_generic,
    'prefab': ssh_tracker,
    'brctl': ssh_brctl,
    'routeros': ssh_routeros,
    'routeros-arp': ssh_routeros_arp,
	'routeros-capsman': ssh_routeros_capsman,
    'zyxel-arp': ssh_zyxel_arp,
    'unifiusg-arp': ssh_unifi_usg_arp,
	'aimesh_json' : ssh_aimesh_json,
    'unifi-http': http_unifi,
    'orbi-http': http_orbi,							#obsolete
    'netgear-soap': soap_netgear,					#prefered for all netgear routers supporting soap, including Orbi
    'omada-http': http_omada,
    'fritzbox': fritzbox,
    'dummy': fake_tracker,
    'missing': test_error_tracker,
    'ping': ping_tracker
}
