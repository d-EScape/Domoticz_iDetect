# Simple tracker for Netgear Orbi
# A crude proof of concept for additional (non-ssh) trackers
# Custom ports are not (yet) supported

import Domoticz
from trackers.tracker_base import tracker
from pynetgear import Netgear

class soap_netgear(tracker):
	def __init__(self, tracker_ip, tracker_port, tracker_user, tracker_password, tracker_keyfile, poll_interval):
		super().__init__(tracker_ip, tracker_port, tracker_user, tracker_password, tracker_keyfile, poll_interval)
		self.prepare_for_polling()
		
	def poll_present_tag_ids(self):
		raw_data = self.netgear.get_attached_devices()
		Domoticz.Debug(self.tracker_ip + ' Returned: ' + raw_data)
		found=[]
		for device in raw_data:
			found.append(device.mac)		
		self.receiver_callback(found)
	
	def prepare_for_polling(self):
		self.netgear = Netgear(password=self.tracker_password)
		self.is_ready = True
		
	def stop_now(self):
		self.is_ready = False
		super().stop_now()