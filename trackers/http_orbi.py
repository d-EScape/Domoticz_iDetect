# Simple tracker for Netgear Orbi
# A crude proof of concept for additional (non-ssh) trackers
# Custom ports are not (yet) supported

import Domoticz
from trackers.tracker_base import tracker
import requests

class http_orbi(tracker):
	def __init__(self, *args, **kwargs):
		super().__init__(*args, **kwargs)
		if self.tracker_port is None:
			self.tracker_port = 443
		self.orbi_url = 'https://{}:{}/DEV_device_info.htm'.format(self.tracker_ip, self.tracker_port)
		self.http_session = None
		self.prepare_for_polling()
		Domoticz.Status('Started address:{}, port:{}, user:{}, keyfile:{}, class:{} and poll interval:{}'.format(self.tracker_ip, self.tracker_port, self.tracker_user, self.tracker_keyfile, self.__class__.__qualname__, self.poll_interval))
		
	def poll_present_tag_ids(self):
		try:
			if not self.http_session:
				self.connect_orbi()
			http_response = self.http_session.get(self.orbi_url, verify=False, timeout=8)
		except Exception as e:
			Domoticz.Error(self.tracker_ip + ' Polling error: ' + str(e))
			try:
				self.http_session.close()
				self.http_session = None
			except Exception as e:
				Domoticz.Debug(self.tracker_ip + ' Close session exception: ' + str(e))
			return
		raw_data = http_response.text
		http_response.close()
		Domoticz.Debug(self.tracker_ip + ' Returned: ' + raw_data)
		self.receiver_callback(raw_data)
			
	def connect_orbi(self):
		self.http_session = requests.Session()
		self.http_session.auth = (self.tracker_user, self.tracker_password)
		self.http_session.keep_alive = False
		Domoticz.Status(self.tracker_ip + ' Initialized as Netgear Orbi')
	
	def prepare_for_polling(self):
		self.connect_orbi()
		self.is_ready = True
		
	def stop_now(self):
		self.is_ready = False
		try:
			self.http_session.close()
			Domoticz.Debug(self.tracker_ip + ' HTTP session closed')
		except Exception as e:
			Domoticz.Error(self.tracker_ip + ' Closing error: ' + str(e))
		super().stop_now()