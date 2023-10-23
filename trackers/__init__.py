import DomoticzEx

def get_tracker(typename="default", **kwargs):
	if kwargs.get('debug',False):
		DomoticzEx.Debugging(62)
		DomoticzEx.Debug("All arguments (except password) for tracker init:" + str({x: kwargs[x] for x in kwargs if x not in ['tracker_password']}))
		DomoticzEx.Debug("Type requested:" + str(typename))
	try:
		if typename == "default":
			from trackers.ssh_autodetect import ssh_autodetect as tracker
		elif typename == "forcegeneric":
			from trackers.ssh_autodetect_generic import ssh_autodetect_generic as tracker
		elif typename == "prefab":
			from trackers.ssh_tracker import ssh_tracker as tracker
		elif typename == "brctl":
			from trackers.ssh_brctl import ssh_brctl as tracker
		elif typename == "routeros":
			from trackers.ssh_routeros import ssh_routeros as tracker
		elif typename == "routeros-arp":
			from trackers.ssh_routeros_arp import ssh_routeros_arp as tracker
		elif typename == "routeros-capsman":
			from trackers.ssh_routeros_capsman import ssh_routeros_capsman as tracker			
		elif typename == "zyxel-arp":
			from trackers.ssh_zyxel_arp import ssh_zyxel_arp as tracker
		elif typename == "unifiusg-arp":
			from trackers.ssh_unifi_usg_arp import ssh_unifi_usg_arp as tracker
		elif typename == "aimesh_json":
			from trackers.ssh_aimesh_json import ssh_aimesh_json as tracker
		elif typename == "unifi-http":
			from trackers.http_unifi import http_unifi as tracker
		elif typename == "orbi-http":
			#Obsolete... use netgear-soap instead (when possible).
			DomoticzEx.Status("Consider using the netgear-soap tracker type instead of the older orbi-http")
			from trackers.http_orbi import http_orbi as tracker
		elif typename == "netgear-soap":
			from trackers.soap_netgear import soap_netgear as tracker			
		elif typename == "omada-http":
			from trackers.http_omada import http_omada as tracker
		elif typename == "fritzbox":
			from trackers.fritzbox import fritzbox as tracker
		elif typename == "dummy":
			from trackers.fake_tracker import fake_tracker as tracker			
		elif typename == "ping":
			from trackers.ping_tracker import ping_tracker as tracker
		else:
			DomoticzEx.Error("There is no tracker type named:" + typename)
			from trackers.unavailable_tracker import unavailable_tracker as tracker	
	except ModuleNotFoundError as moderr: 
		DomoticzEx.Error("Required modules for " + typename + " tracker are not installed:" + str(moderr))
		from trackers.unavailable_tracker import unavailable_tracker as tracker
	except Exception as err:
		DomoticzEx.Error("Error while trying to import tracker module:" + str(err))
		from trackers.unavailable_tracker import unavailable_tracker as tracker
	DomoticzEx.Debug("Trackertype '" + typename +"' got router module: " + str(tracker.__name__))			
	return tracker(**kwargs)