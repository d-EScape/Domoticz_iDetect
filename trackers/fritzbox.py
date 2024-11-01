# Tracker for Fritzbox and tested on Fritzbox 4060
# Needs fritzconnection by Klaus Bremer et al, so make sure you did: pip install fritzconnection

import DomoticzEx
from trackers.tracker_base import tracker
from fritzconnection import FritzConnection
from fritzconnection.lib.fritzhosts import FritzHosts
from time import sleep

class fritzbox(tracker):
	def __init__(self, *args, **kwargs):
		super().__init__(*args, **kwargs)
		self.busy = False
		self.prepare_for_polling()
		
	def poll_present_tag_ids(self):
		self.busy = True
		listofhosts=[]
		listofactivehosts=[]
		try:
			listofhosts = self.fritzlist.get_hosts_info()
		except Exception as e:
			DomoticzEx.Error(self.tracker_ip + ' Fritzbox polling error: ' + str(e))
			self.prepare_for_polling()
		else:
			for host in listofhosts:
				if host['status']==True:
					listofactivehosts.append(host['mac'])
			self.receiver_callback(listofactivehosts)
		self.busy = False
		
	def prepare_for_polling(self):
		try:
			self.session = FritzConnection(address=self.tracker_ip, user=self.tracker_user, password=self.tracker_password)
			self.fritzlist = FritzHosts(self.session)
		except Exception as e:
			DomoticzEx.Log('Fritzbox ' + self.tracker_ip + ' failed to connect. Check your setup and restart the plugin.')
			DomoticzEx.Debug(e)
		else:
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
