# Tracker for Netgear routers supporting Simple Object Access Protocol (soap) interface, including Orbi
# Have a look at https://github.com/MatMaul/pynetgear for supported routers
# Default user on netgear routers is 'admin' (all lower case)
# The routers needs to be on the same LAN as Domoticz
#
# !!! The plugin assumes a ssl connection and defaults to port 443. You can change the port, but it has to be ssl (like 5555 on some routers).
# !!! If you set 'autodetect' as hostname then the plugin will leave the search for a netgear router up to the pynetgear module

import DomoticzEx
from trackers.tracker_base import tracker
from pynetgear import Netgear
import requests

class soap_netgear(tracker):
	def __init__(self, *args, **kwargs):
		super().__init__(*args, **kwargs)
		if self.tracker_port is None:
			self.tracker_port = 443
		self.prepare_for_polling()
		
	def poll_present_tag_ids(self):
		try:
			raw_data = self.netgear.get_attached_devices()
		except Exception as e:
			DomoticzEx.Error(e)
			raw_data = []
		DomoticzEx.Debug(self.tracker_ip + ' Returned: ' + str(raw_data))
		found=[]
		for device in raw_data:
			found.append(device.mac)		
		self.receiver_callback(found)
	
	def prepare_for_polling(self):
		if self.tracker_ip.lower() == "autodetect":
			self.netgear = Netgear(password=self.tracker_password, user=self.tracker_user)
			DomoticzEx.Log('Will search for netgear router with soap interface...')
		else:
			self.netgear = Netgear(password=self.tracker_password, host=self.tracker_ip, ssl=True, port=self.tracker_port, user=self.tracker_user)
			DomoticzEx.Log(self.tracker_ip + ' configured for soap access')
		self.is_ready = True
		
	def stop_now(self):
		self.is_ready = False
		self.netgear = None
		super().stop_now()