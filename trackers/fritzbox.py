# Tracker for Fritzbox and tested on Fritzbox 7590
# Needs fritzconnection by Klaus Bremer, so make sure you did: pip install fritzconnection
# Should work on other models. The number of wlans's is automatically detected.

import Domoticz
from trackers.tracker_base import tracker
try:
	from fritzconnection import FritzConnection
	from fritzconnection.lib.fritzwlan import FritzWLAN
	from fritzconnection.core.exceptions import FritzServiceError
except ImportError as e:
	Domoticz.Error('Failed to load iDetect. The fritzconnection python module is required. ' + str(e))

class fritzbox(tracker):
	def __init__(self, tracker_ip, tracker_port, tracker_user, tracker_password, tracker_keyfile, poll_interval):
		super().__init__(tracker_ip, tracker_port, tracker_user, tracker_password, tracker_keyfile, poll_interval)
		self.tracker_ip = tracker_ip
		self.tracker_password = tracker_password
		self.wlans = []
		self.prepare_for_polling()
		
	def poll_present_tag_ids(self):
		listofhosts=[]
		listofactivehosts=[]
		try:
			for wlan in self.wlans:
				listofhosts = listofhosts + wlan.get_hosts_info()
		except Exception as e:
			Domoticz.Error(self.tracker_ip + ' Fritzbox polling error: ' + str(e))
		for host in listofhosts:
			if host['status']==True:
				listofactivehosts.append(host['mac'])
		self.receiver_callback(listofactivehosts)
		
	def prepare_for_polling(self):
		try:
			self.session = FritzConnection(address=self.tracker_ip, password=self.tracker_password)
		except Exception as e:
			Domoticz.Log('Fritzbox ' + self.tracker_ip + ' failed to connect. Check your setup and restart the plugin.')
			Domoticz.Debug(e)
		else:
			servicenum=1
			reachedend=False
			while not reachedend:
				newwlan = FritzWLAN(self.session, service=servicenum)
				try:
					ssid = newwlan.ssid
				except Exception as e:
					reachedend = True
					Domoticz.Debug('Fritzbox does not have service ' + str(servicenum))
					Domoticz.Debug(e)
				else:
					self.wlans.append(newwlan)
					Domoticz.Debug('Fritzbox has service ' + str(servicenum) + ' with SSID ' + ssid)
					servicenum=servicenum+1
					if servicenum > 10: 	#failsave to prevent endless searches
						reachedend = True
			Domoticz.Status('Fritzbox has ' + str(servicenum-1) + ' WLAN services')
			self.is_ready = True
		
	def stop_now(self):
		self.is_ready = False
		self.wlans=[]
		self.session = None
		super().stop_now()
				
				
