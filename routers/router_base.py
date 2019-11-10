import Domoticz
import threading
import helpers.data_helper as data_helper
from time import sleep
from datetime import datetime, timedelta


class router():
	def __init__(self, router_ip, router_port, router_user, router_password, router_keyfile, poll_interval):
		self.router_ip = router_ip
		self.router_port = router_port
		self.router_user = router_user
		self.router_password = router_password
		self.router_keyfile = router_keyfile
		self.poll_interval = poll_interval
		self.found_macs = []
		self.last_update = datetime.now()
		self.error_state = False
		self.is_ready = False
		self.poll_timer = None
		self.interpreter_callback = None
		self.error_count = 0
#		self.poll_timer = threading.Timer(self.poll_interval, self.initiate_poll)
#		self.poll_timer.start()
			
	def heartbeat_handler(self):
		seconds_ago = data_helper.time_since_last(self.last_update)
		Domoticz.Debug(str(self.router_ip) + ' Last poll was ' + str(seconds_ago) + ' seconds ago')
		if seconds_ago > self.poll_interval:
			self.initiate_poll()
	
	def receiver_callback(self, raw_data):
		self.found_macs = data_helper.clean_mac_list(raw_data)
		if not self.interpreter_callback is None:
			self.interpreter_callback(self)
		else:
			Domoticz.Debug(self.router_ip + ' No interpreter_callback registered. Ignoring new data.')
		Domoticz.Debug(self.router_ip + ' Polling done')
		
	def initiate_poll(self):
		if self.is_ready:
			poll_thread = threading.Thread(target=self.poll_present_macs())
			poll_thread.start()
		else:
			Domoticz.Log(self.router_ip + ' not (yet) ready for polling')
#		self.poll_timer = threading.Timer(self.poll_interval, self.initiate_poll)
#		self.poll_timer.start()
		self.last_update = datetime.now()
		
	def poll_present_macs(self):
		Domoticz.Debug(self.router_ip + ' Has no polling method defined')
		
	def stop_now(self):
		if not self.poll_timer is None:
			self.poll_timer.cancel()
		Domoticz.Debug(self.router_ip + ' Polling canceled')
		self.is_ready = False
		
	def register_list_interpreter(self, callback):
		self.interpreter_callback=callback
		Domoticz.Debug(self.router_ip + ' Data will be received and interpreted by ' + str(self.interpreter_callback))
		