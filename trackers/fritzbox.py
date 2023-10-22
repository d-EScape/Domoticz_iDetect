# Tracker for Fritzbox and tested on Fritzbox 7590
# Needs fritzconnection by Klaus Bremer, so make sure you did: pip install fritzconnection
# Should work on other models. The number of wlans's is automatically detected.

import DomoticzEx
from trackers.tracker_base import tracker
from fritzconnection import FritzConnection
from fritzconnection.lib.fritzwlan import FritzWLAN
from time import sleep

class fritzbox(tracker):
	def __init__(self, *args, **kwargs):
		super().__init__(*args, **kwargs)
		self.busy = False
		self.wlans = []
		self.prepare_for_polling()
		
	def poll_present_tag_ids(self):
		self.busy = True
		listofhosts=[]
		listofactivehosts=[]
		try:
			for wlan in self.wlans:
				listofhosts = listofhosts + wlan.get_hosts_info()
		except Exception as e:
			DomoticzEx.Error(self.tracker_ip + ' Fritzbox polling error: ' + str(e))
		for host in listofhosts:
			if host['status']==True:
				listofactivehosts.append(host['mac'])
		self.receiver_callback(listofactivehosts)
		self.busy = False
		
	def prepare_for_polling(self):
		try:
			self.session = FritzConnection(address=self.tracker_ip, password=self.tracker_password)
		except Exception as e:
			DomoticzEx.Log('Fritzbox ' + self.tracker_ip + ' failed to connect. Check your setup and restart the plugin.')
			DomoticzEx.Debug(e)
		else:
			servicenum=1
			reachedend=False
			while not reachedend:
				newwlan = FritzWLAN(self.session, service=servicenum)
				try:
					ssid = newwlan.ssid
				except Exception as e:
					reachedend = True
					DomoticzEx.Debug('Fritzbox does not have service ' + str(servicenum))
					DomoticzEx.Debug(e)
				else:
					self.wlans.append(newwlan)
					DomoticzEx.Debug('Fritzbox has service ' + str(servicenum) + ' with SSID ' + ssid)
					servicenum=servicenum+1
					if servicenum > 10: 	#failsave to prevent endless searches
						reachedend = True
			DomoticzEx.Status('Fritzbox has ' + str(servicenum-1) + ' WLAN services')
			self.is_ready = True				

	def stop_now(self):
		self.is_ready = False
		waitcounter = 0
		maxwait = 100
		while self.busy and waitcounter < maxwait:
			waitcounter = waitcounter + 1
			sleep(0.05)
		if waitcounter < maxwait:
			DomoticzEx.Debug("Fritbox polling stopped in time (counter at {})".format(waitcounter))
		else:
			DomoticzEx.Status("Fritbox tracker forced to stop during poll (wait time exceeded)")
		self.wlans=[]
		self.session = None
		super().stop_now()